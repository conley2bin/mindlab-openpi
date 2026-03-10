#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
from collections import OrderedDict
from datetime import date


PROGRESS_DOC_PREFIXES = (
    "workspace/docs/targets/",
    "workspace/docs/plans/",
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


def _run_git(repo_root: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _collect_same_day_commits(repo_root: pathlib.Path, target_date: str) -> list[dict[str, object]]:
    raw = _run_git(repo_root, "log", "--format=%H%x00%s%x00%aI")
    commits: list[dict[str, object]] = []
    for line in raw.splitlines():
        if not line:
            continue
        commit_hash, subject, author_date = line.split("\x00")
        if not author_date.startswith(target_date):
            continue
        touched_paths = _collect_commit_paths(repo_root, commit_hash)
        commits.append(
            {
                "hash": commit_hash,
                "subject": subject,
                "author_date": author_date,
                "touched_paths": sorted(touched_paths),
            }
        )
    commits.sort(key=lambda item: str(item["author_date"]))
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


def _collect_progress_docs(commits: list[dict[str, object]]) -> tuple[list[str], dict[str, str]]:
    doc_to_commit: dict[str, str] = {}
    ordered_docs: list[str] = []
    for commit in commits:
        commit_hash = str(commit["hash"])
        for path in sorted(str(path) for path in commit["touched_paths"]):
            if not path.startswith(PROGRESS_DOC_PREFIXES):
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
        if source_path.startswith("workspace/docs/plans/") and stripped.startswith("Run:"):
            command = _extract_first_command(stripped)
            if command is not None:
                commands.append(command)
            continue
        if source_path.startswith("workspace/docs/targets/"):
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


def _extract_facts_from_progress_doc(
    path: str,
    text: str,
    verification_commands: list[str],
) -> list[dict[str, object]]:
    theme_hint = _extract_theme_hint(path, text)
    facts: list[dict[str, object]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
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


def collect_daily_report_facts(repo_root: pathlib.Path, target_date: str) -> dict[str, object]:
    commits = _collect_same_day_commits(repo_root, target_date)
    progress_docs, doc_to_commit = _collect_progress_docs(commits)

    doc_texts = {
        path: _read_committed_file(repo_root, doc_to_commit[path], path)
        for path in progress_docs
    }
    verification_commands = _dedupe_preserve_order(
        [
            command
            for path in progress_docs
            for command in _extract_commands_from_text(doc_texts[path], path)
        ]
    )

    facts: list[dict[str, object]] = []
    for path in progress_docs:
        if not path.startswith("workspace/docs/targets/"):
            continue
        path_commands = _extract_commands_from_text(doc_texts[path], path)
        facts.extend(_extract_facts_from_progress_doc(path, doc_texts[path], path_commands or verification_commands))
    facts.extend(_extract_commit_facts(commits))

    return {
        "date": target_date,
        "commits": commits,
        "progress_docs": progress_docs,
        "facts": facts,
        "verification_commands": verification_commands,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--json-indent", type=int, default=None)
    args = parser.parse_args()

    payload = collect_daily_report_facts(args.repo_root.resolve(), args.target_date)
    print(json.dumps(payload, ensure_ascii=False, indent=args.json_indent))


if __name__ == "__main__":
    main()
