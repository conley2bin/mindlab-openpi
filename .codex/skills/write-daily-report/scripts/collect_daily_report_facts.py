#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
from collections import OrderedDict
from datetime import date
from datetime import datetime
from typing import Any


PROGRESS_DOC_PREFIXES = (
    "docs/targets/",
    "docs/plans/",
    "docs/progress/",
)

COMMAND_PREFIXES = (
    "python",
    "python3",
    "pytest",
    "uv ",
    "uvx ",
    "bash ",
    "sh ",
    "make ",
    "npm ",
    "pnpm ",
    "cargo ",
    "go ",
)

COMMAND_TOKENS = (
    "pytest",
    "python -m unittest",
    "python3 -m unittest",
    "uv run",
    "ruff check",
    "npm test",
    "pnpm test",
    "cargo test",
    "go test",
    "make test",
)


PROFESSIONAL_REPORT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
HUMAN_AUTHOR_DATE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{2}:\d{2}$"
)


class DailyReportRangeError(RuntimeError):
    pass


def _run_git_cwd(cwd: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _run_git(repo_root: pathlib.Path, *args: str) -> str:
    return _run_git_cwd(repo_root, *args)


def _git_object_exists(cwd: pathlib.Path, rev: str) -> bool:
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"{rev}^{{object}}"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _format_author_date(value: str) -> str:
    if HUMAN_AUTHOR_DATE_RE.fullmatch(value.strip()):
        return value.strip()
    try:
        dt = datetime.fromisoformat(value.strip())
    except ValueError:
        return value
    offset = dt.strftime("%z")
    if offset:
        offset = f"{offset[:3]}:{offset[3:]}"
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {offset}"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _verify_commitish(repo_root: pathlib.Path, rev: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", f"{rev}^{{commit}}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise DailyReportRangeError(
            f"start_commit '{rev}' cannot be resolved by git rev-parse --verify"
        )
    return proc.stdout.strip()


def _collect_head_commits(repo_root: pathlib.Path) -> list[dict[str, object]]:
    raw = _run_git(repo_root, "log", "--reverse", "--format=%H%x00%s%x00%aI", "HEAD")
    commits: list[dict[str, object]] = []
    for line in raw.splitlines():
        if not line:
            continue
        commit_hash, subject, author_date = line.split("\x00")
        commits.append(
            {
                "hash": commit_hash,
                "subject": subject,
                "author_date": author_date,
            }
        )
    return commits


def _collect_commit_paths(repo_root: pathlib.Path, commit_hash: str) -> list[str]:
    paths: list[str] = []
    raw = _run_git(repo_root, "show", "--name-status", "--format=", commit_hash)
    for line in raw.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("D"):
            continue
        if status.startswith(("R", "C")):
            paths.append(parts[-1])
            continue
        paths.append(parts[-1])
    return [path for path in paths if path]


def _collect_gitlink_updates(repo_root: pathlib.Path, commit_hash: str) -> list[dict[str, str]]:
    raw = _run_git(repo_root, "diff-tree", "-r", "--raw", "--no-commit-id", commit_hash)
    updates: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line or "\t" not in line:
            continue
        meta, path = line.split("\t", 1)
        parts = meta.split()
        if len(parts) != 5:
            continue
        old_mode = parts[0].lstrip(":")
        new_mode = parts[1]
        old_sha = parts[2]
        new_sha = parts[3]
        status = parts[4]
        if old_mode != "160000" and new_mode != "160000":
            continue
        updates.append(
            {
                "path": path,
                "old_sha": old_sha,
                "new_sha": new_sha,
                "status": status,
            }
        )
    return updates


def _is_reportable_doc_path(path: str) -> bool:
    return path.startswith(PROGRESS_DOC_PREFIXES) and pathlib.Path(path).name != "README.md"


def _list_daily_reports(repo_root: pathlib.Path, target_date: str) -> list[pathlib.Path]:
    report_dir = repo_root / "docs/daily-report"
    if not report_dir.exists():
        return []
    reports: list[pathlib.Path] = []
    for path in sorted(report_dir.iterdir()):
        if not path.is_file():
            continue
        if not PROFESSIONAL_REPORT_RE.fullmatch(path.name):
            continue
        if path.stem >= target_date:
            continue
        reports.append(path)
    return reports


def _parse_front_matter(text: str) -> dict[str, str]:
    match = FRONT_MATTER_RE.match(text)
    if match is None:
        return {}
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def _find_previous_report(repo_root: pathlib.Path, target_date: str) -> pathlib.Path | None:
    reports = _list_daily_reports(repo_root, target_date)
    if not reports:
        return None
    return reports[-1]


def _resolve_commit_range(
    repo_root: pathlib.Path,
    target_date: str,
    start_commit: str | None,
) -> tuple[list[dict[str, object]], str, pathlib.Path | None]:
    all_commits = _collect_head_commits(repo_root)
    if not all_commits:
        raise DailyReportRangeError("repository has no commits on HEAD")

    commit_order = [str(commit["hash"]) for commit in all_commits]
    commit_index = {commit_hash: i for i, commit_hash in enumerate(commit_order)}
    previous_report = _find_previous_report(repo_root, target_date)

    if start_commit is not None:
        resolved_start = _verify_commitish(repo_root, start_commit)
        if resolved_start not in commit_index:
            raise DailyReportRangeError(
                f"start_commit '{start_commit}' resolves to {resolved_start}, which is not reachable from HEAD"
            )
        selected = all_commits[commit_index[resolved_start] :]
        return selected, "manual", previous_report

    if previous_report is None:
        raise DailyReportRangeError(
            "no previous daily report found before the target date; provide --start-commit"
        )

    metadata = _parse_front_matter(previous_report.read_text(encoding="utf-8"))
    previous_end = metadata.get("range_end_commit")
    if not previous_end:
        raise DailyReportRangeError(
            f"previous daily report {previous_report} is missing range_end_commit; provide --start-commit"
        )
    resolved_previous_end = _verify_commitish(repo_root, previous_end)
    if resolved_previous_end not in commit_index:
        raise DailyReportRangeError(
            f"previous report range_end_commit {resolved_previous_end} is not reachable from HEAD; provide --start-commit"
        )

    start_index = commit_index[resolved_previous_end] + 1
    selected = all_commits[start_index:]
    return selected, "auto", previous_report


def _collect_progress_docs(commits: list[dict[str, object]]) -> tuple[list[str], dict[str, str]]:
    doc_to_commit: dict[str, str] = {}
    ordered_docs: list[str] = []
    for commit in commits:
        commit_hash = str(commit["hash"])
        for path in sorted(str(path) for path in commit["touched_paths"]):
            if not _is_reportable_doc_path(path):
                continue
            if path not in doc_to_commit:
                ordered_docs.append(path)
            doc_to_commit[path] = commit_hash
    return ordered_docs, doc_to_commit


def _read_committed_file(repo_root: pathlib.Path, commit_hash: str, path: str) -> str:
    return _run_git(repo_root, "show", f"{commit_hash}:{path}")


def _extract_commands_from_text(text: str, source_path: str) -> list[str]:
    commands: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Run:"):
            command = _extract_first_command(stripped)
            if command is not None:
                commands.append(command)
            continue
        if source_path.startswith("docs/targets/"):
            command = _extract_first_command(stripped)
            if command is not None:
                commands.append(command)
    return commands


def _extract_first_command(text: str) -> str | None:
    backtick_match = re.search(r"`([^`]+)`", text)
    if backtick_match is not None:
        candidate = backtick_match.group(1).strip()
        if _looks_like_command(candidate):
            return candidate
    candidate = text.removeprefix("Run:").strip()
    if _looks_like_command(candidate):
        return candidate
    return None


def _looks_like_command(candidate: str) -> bool:
    if candidate.startswith(COMMAND_PREFIXES):
        return True
    return any(token in candidate for token in COMMAND_TOKENS)


def _is_test_path(path: str) -> bool:
    name = pathlib.Path(path).name
    return (
        "/tests/" in f"/{path}"
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".spec.ts")
        or name.endswith(".test.ts")
        or name.endswith(".spec.tsx")
        or name.endswith(".test.tsx")
    )


def _infer_change_kind(repo: str, changed_files: list[str], changed_tests: list[str]) -> str:
    if any("/.github/workflows/" in f or f.startswith(".github/workflows/") for f in changed_files):
        return "ci"
    if any("remote_deployment_smoke" in f or "live_service_smoke" in f for f in changed_files):
        return "validation"
    if any("cross_repo_closed_loop" in f or "runtime_bridge" in f for f in changed_files):
        return "validation"
    if repo == "src/openpi" and any("src/openpi/integration/" in f for f in changed_files):
        return "runtime"
    if repo == "src/mint" and any("tinker_server/openpi/" in f for f in changed_files):
        return "service"
    if repo == "src/mindlab-toolkit" and any("src/mint/openpi/" in f for f in changed_files):
        return "sdk"
    if changed_tests and len(changed_tests) == len(changed_files):
        return "tests"
    if all(f.startswith(("docs/", ".codex/skills/")) for f in changed_files):
        return "docs"
    return "code"


def _infer_capability_hint(repo: str, changed_files: list[str], subject: str) -> str:
    lowered_subject = subject.lower()
    if any("remote_deployment_smoke" in f for f in changed_files):
        return "remote deployment smoke"
    if any("live_service_smoke" in f for f in changed_files):
        return "localhost live-service smoke"
    if any("cross_repo_closed_loop" in f for f in changed_files):
        return "cross-repo closed loop"
    if any("runtime_bridge" in f for f in changed_files):
        return "Mint runtime bridge"
    if repo == "src/openpi" and any("src/openpi/integration/" in f for f in changed_files):
        return "OpenPI runtime facade"
    if repo == "src/mint" and any("tinker_server/openpi/" in f for f in changed_files):
        return "Mint OpenPI service plane"
    if repo == "src/mindlab-toolkit" and any("src/mint/openpi/" in f for f in changed_files):
        return "Toolkit OpenPI SDK"
    if any("st-08" in f or "remote" in lowered_subject for f in changed_files):
        return "remote validation and failure attribution"
    if any("st-07" in f or "capability" in lowered_subject for f in changed_files):
        return "capability negotiation"
    if any("st-06" in f or "validation-baseline" in f for f in changed_files):
        return "operational hardening and release discipline"
    if any(f.startswith("docs/") for f in changed_files):
        return "OpenPI planning and progress docs"
    if any(f.startswith(".codex/skills/") for f in changed_files):
        return "daily report skill"
    return repo


def _normalize_pytest_command(command: str) -> str:
    if "pytest" not in command:
        return command
    tokens = command.split()
    filtered: list[str] = []
    has_verbose = False
    has_report = False
    for token in tokens:
        if token in {"-q", "--quiet"}:
            continue
        if token in {"-v", "-vv", "-vvv", "--verbose"}:
            has_verbose = True
        if token.startswith("-r") and len(token) > 2:
            has_report = True
        filtered.append(token)
    if not has_verbose:
        filtered.append("-vv")
    if not has_report:
        filtered.append("-ra")
    return " ".join(filtered)


def _build_test_command(repo_root: pathlib.Path, repo: str, test_path: str) -> str | None:
    pytest_bin = repo_root / repo / ".venv/bin/pytest"
    python_bin = repo_root / repo / ".venv/bin/python"
    if repo == "src/openpi":
        command = f"cd {repo} && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest {test_path}"
        return _normalize_pytest_command(command)
    if repo == "src/mint":
        if pytest_bin.exists():
            command = f"cd {repo} && .venv/bin/pytest {test_path}"
            return _normalize_pytest_command(command)
        if python_bin.exists():
            command = f"cd {repo} && .venv/bin/python -m pytest {test_path}"
            return _normalize_pytest_command(command)
        command = f"cd {repo} && python3 -m pytest {test_path}"
        return _normalize_pytest_command(command)
    if repo == "src/mindlab-toolkit":
        if pytest_bin.exists():
            command = f"cd {repo} && .venv/bin/pytest {test_path}"
            return _normalize_pytest_command(command)
        if python_bin.exists():
            command = f"cd {repo} && .venv/bin/python -m pytest {test_path}"
            return _normalize_pytest_command(command)
        command = f"cd {repo} && python3 -m pytest {test_path}"
        return _normalize_pytest_command(command)
    if test_path.endswith(".py"):
        return _normalize_pytest_command(f"python3 -m pytest {test_path}")
    return None


def _verification_commands_from_code_evidence(
    repo_root: pathlib.Path,
    entry: dict[str, Any],
) -> list[str]:
    commands: list[str] = []
    for test_path in entry.get("changed_tests", [])[:2]:
        command = _build_test_command(repo_root, str(entry["repo"]), str(test_path))
        if command is not None:
            commands.append(command)
    return commands


def _summarize_file_list(paths: list[str], limit: int = 4) -> str:
    preview = ", ".join(f"`{path}`" for path in paths[:limit])
    if len(paths) > limit:
        return f"{preview} and {len(paths) - limit} more files"
    return preview


def _code_evidence_to_fact(repo_root: pathlib.Path, entry: dict[str, Any]) -> dict[str, Any]:
    files_summary = _summarize_file_list(list(entry["changed_files"]))
    statement = f"在 `{entry['repo']}` 修改了 {files_summary}"
    if entry.get("changed_tests"):
        statement += f"，测试锚点包括 {_summarize_file_list(list(entry['changed_tests']), limit=3)}"
    statement += f"，对应能力是 {entry['capability_hint']}。"
    return {
        "theme_hint": str(entry["capability_hint"]),
        "source_type": "code_evidence",
        "source_id": str(entry["commit"]),
        "statement": statement,
        "status": "progress",
        "verification_command_candidates": _verification_commands_from_code_evidence(repo_root, entry),
    }


def _collect_root_code_evidence(
    commit: dict[str, Any],
    submodule_paths: set[str],
) -> list[dict[str, Any]]:
    changed_files = [
        str(path)
        for path in commit["touched_paths"]
        if str(path) not in submodule_paths
    ]
    if not changed_files:
        return []
    changed_tests = [path for path in changed_files if _is_test_path(path)]
    return [
        {
            "commit": str(commit["hash"]),
            "author_date": str(commit["author_date"]),
            "subject": str(commit["subject"]),
            "repo": "repo-root",
            "changed_files": changed_files,
            "changed_tests": changed_tests,
            "change_kind": _infer_change_kind("repo-root", changed_files, changed_tests),
            "capability_hint": _infer_capability_hint("repo-root", changed_files, str(commit["subject"])),
        }
    ]


def _collect_submodule_code_evidence(
    repo_root: pathlib.Path,
    submodule_path: str,
    old_sha: str,
    new_sha: str,
    subject: str = "",
    commit_hash: str = "",
    author_date: str = "",
) -> list[dict[str, Any]]:
    if old_sha == "0" * 40 or new_sha == "0" * 40:
        return []
    submodule_root = repo_root / submodule_path
    if not submodule_root.exists():
        return []
    if not _git_object_exists(submodule_root, old_sha):
        return []
    if not _git_object_exists(submodule_root, new_sha):
        return []
    raw = _run_git_cwd(submodule_root, "diff", "--name-status", old_sha, new_sha)
    changed_files: list[str] = []
    for line in raw.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if parts[0].startswith("D"):
            continue
        changed_files.append(parts[-1])
    if not changed_files:
        return []
    changed_tests = [path for path in changed_files if _is_test_path(path)]
    return [
        {
            "commit": commit_hash,
            "author_date": author_date,
            "subject": subject,
            "repo": submodule_path,
            "changed_files": changed_files,
            "changed_tests": changed_tests,
            "change_kind": _infer_change_kind(submodule_path, changed_files, changed_tests),
            "capability_hint": _infer_capability_hint(submodule_path, changed_files, subject),
            "submodule_old_sha": old_sha,
            "submodule_new_sha": new_sha,
        }
    ]


def _collect_code_evidence(repo_root: pathlib.Path, commits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for commit in commits:
        gitlink_updates = _collect_gitlink_updates(repo_root, str(commit["hash"]))
        submodule_paths = {str(update["path"]) for update in gitlink_updates}
        evidence.extend(_collect_root_code_evidence(commit, submodule_paths))
        for update in gitlink_updates:
            evidence.extend(
                _collect_submodule_code_evidence(
                    repo_root,
                    str(update["path"]),
                    str(update["old_sha"]),
                    str(update["new_sha"]),
                    subject=str(commit["subject"]),
                    commit_hash=str(commit["hash"]),
                    author_date=str(commit["author_date"]),
                )
            )
    return evidence


def _extract_facts_from_doc(
    path: str,
    text: str,
    verification_commands: list[str],
) -> list[dict[str, object]]:
    theme_hint = _extract_theme_hint(path, text)
    facts: list[dict[str, object]] = []
    current_section: str | None = None
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("## "):
            current_section = stripped[3:].strip()
            continue
        if stripped.startswith(("#", "|")):
            continue
        if stripped.startswith("Run:"):
            continue
        if stripped.startswith(("- ", "* ")):
            statement = stripped[2:].strip()
        elif re.match(r"^\d+\.\s+", stripped):
            statement = re.sub(r"^\d+\.\s+", "", stripped)
        else:
            continue
        if statement.startswith("Status:"):
            continue
        if not _should_include_fact_section(path, current_section):
            continue
        status = _classify_status(statement)
        if status == "note":
            continue
        facts.append(
            {
                "theme_hint": theme_hint,
                "source_type": "progress_doc",
                "source_id": path,
                "statement": statement,
                "status": status,
                "verification_command_candidates": verification_commands,
            }
        )
    return facts


def _extract_theme_hint(path: str, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return pathlib.Path(path).stem


def _should_include_fact_section(path: str, current_section: str | None) -> bool:
    if path.startswith("docs/progress/"):
        return True
    if not path.startswith("docs/targets/subtarget-"):
        return False
    if current_section is None:
        return False
    return current_section.startswith("Current ")


def _classify_status(statement: str) -> str:
    progress_tokens = (
        "不再",
        "已",
        "支持",
        "完成",
        "补齐",
        "新增",
        "接通",
        "接入",
        "通过",
        "恢复",
        "暴露",
        "透传",
        "收口",
        "显式拒绝",
        "显式声明",
    )
    issue_tokens = (
        "失败",
        "仍有",
        "仍拿不到",
        "缺",
        "问题",
        "卡",
        "阻塞",
        "无法",
        "不能",
        "不包含",
        "不适合",
        "不负责",
        "不是",
    )
    if any(token in statement for token in progress_tokens):
        return "progress"
    if any(token in statement for token in issue_tokens):
        return "issue"
    return "note"


def _extract_commit_facts(commits: list[dict[str, object]]) -> list[dict[str, object]]:
    facts: list[dict[str, object]] = []
    for commit in commits:
        facts.append(
            {
                "theme_hint": str(commit["subject"]),
                "source_type": "commit",
                "source_id": str(commit["hash"]),
                "statement": str(commit["subject"]),
                "status": "progress",
                "verification_command_candidates": [],
            }
        )
    return facts


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    return list(OrderedDict.fromkeys(items))


def _is_fact_source_path(path: str) -> bool:
    if path.startswith("docs/progress/"):
        return True
    return path.startswith("docs/targets/subtarget-")


def collect_daily_report_facts(
    repo_root: pathlib.Path,
    target_date: str,
    start_commit: str | None = None,
) -> dict[str, object]:
    commits, range_mode, previous_report = _resolve_commit_range(repo_root, target_date, start_commit)
    if not commits:
        if range_mode == "auto" and previous_report is not None:
            raise DailyReportRangeError(
                f"previous report {previous_report} already ends at current HEAD; no new commits in range"
            )
        raise DailyReportRangeError("specified commit range contains no new commits")

    commits = [
        {
            **commit,
            "author_date": _format_author_date(str(commit["author_date"])),
            "touched_paths": sorted(_collect_commit_paths(repo_root, str(commit["hash"]))),
        }
        for commit in commits
    ]
    code_evidence = _collect_code_evidence(repo_root, commits)
    progress_docs, doc_to_commit = _collect_progress_docs(commits)

    doc_texts = {
        path: _read_committed_file(repo_root, doc_to_commit[path], path)
        for path in progress_docs
    }
    doc_commands = _dedupe_preserve_order(
        [
            command
            for path in progress_docs
            for command in _extract_commands_from_text(doc_texts[path], path)
        ]
    )
    code_commands = _dedupe_preserve_order(
        [
            command
            for entry in code_evidence
            for command in _verification_commands_from_code_evidence(repo_root, entry)
        ]
    )
    verification_commands = _dedupe_preserve_order(doc_commands + code_commands)

    facts: list[dict[str, object]] = []
    facts.extend(_code_evidence_to_fact(repo_root, entry) for entry in code_evidence)
    for path in progress_docs:
        if not _is_fact_source_path(path):
            continue
        path_commands = _extract_commands_from_text(doc_texts[path], path)
        facts.extend(_extract_facts_from_doc(path, doc_texts[path], path_commands or verification_commands))
    facts.extend(_extract_commit_facts(commits))

    return {
        "date": target_date,
        "range_mode": range_mode,
        "previous_report": str(previous_report) if previous_report is not None else None,
        "range_start_commit": str(commits[0]["hash"]),
        "range_start_author_date": str(commits[0]["author_date"]),
        "range_end_commit": str(commits[-1]["hash"]),
        "range_end_author_date": str(commits[-1]["author_date"]),
        "commits": commits,
        "code_evidence": code_evidence,
        "progress_docs": progress_docs,
        "facts": facts,
        "verification_commands": verification_commands,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--start-commit")
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--json-indent", type=int, default=None)
    args = parser.parse_args()

    try:
        payload = collect_daily_report_facts(
            args.repo_root.resolve(),
            args.target_date,
            start_commit=args.start_commit,
        )
    except DailyReportRangeError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(payload, ensure_ascii=False, indent=args.json_indent))


if __name__ == "__main__":
    main()
