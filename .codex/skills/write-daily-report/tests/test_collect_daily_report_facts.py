from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "collect_daily_report_facts.py"
)
SPEC = importlib.util.spec_from_file_location("collect_daily_report_facts", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_collect_daily_report_facts_emits_code_evidence(monkeypatch):
    commits = [
        {
            "hash": "abc123",
            "subject": "Add Mint OpenPI service plane",
            "author_date": "2026-03-12T10:00:00+08:00",
        }
    ]

    monkeypatch.setattr(
        MODULE,
        "_resolve_commit_range",
        lambda repo_root, target_date, start_commit: (commits, "manual", None),
    )
    monkeypatch.setattr(MODULE, "_collect_commit_paths", lambda repo_root, commit_hash: ["src/mint"])
    monkeypatch.setattr(MODULE, "_collect_gitlink_updates", lambda repo_root, commit_hash: [])
    monkeypatch.setattr(MODULE, "_collect_progress_docs", lambda commits: ([], {}))

    payload = MODULE.collect_daily_report_facts(Path.cwd(), "2026-03-12", start_commit="abc123")

    assert "code_evidence" in payload
    assert payload["code_evidence"]
    assert payload["range_start_author_date"] == "2026-03-12 10:00:00 +08:00"
    assert payload["range_end_author_date"] == "2026-03-12 10:00:00 +08:00"
    assert not payload["facts"][0]["statement"].startswith("abc123")


def test_collect_daily_report_facts_derives_verification_commands_from_code_evidence(monkeypatch):
    commits = [
        {
            "hash": "def456",
            "subject": "Add localhost live smoke",
            "author_date": "2026-03-12T11:00:00+08:00",
        }
    ]

    monkeypatch.setattr(
        MODULE,
        "_resolve_commit_range",
        lambda repo_root, target_date, start_commit: (commits, "manual", None),
    )
    monkeypatch.setattr(
        MODULE,
        "_collect_commit_paths",
        lambda repo_root, commit_hash: ["src/mint"],
    )
    monkeypatch.setattr(MODULE, "_collect_progress_docs", lambda commits: ([], {}))
    monkeypatch.setattr(
        MODULE,
        "_collect_submodule_code_evidence",
        lambda repo_root, submodule_path, old_sha, new_sha, subject="", commit_hash="", author_date="": [
            {
                "commit": commit_hash,
                "author_date": author_date,
                "subject": subject,
                "repo": "src/mint",
                "changed_files": ["tests/test_openpi_live_service_smoke.py"],
                "changed_tests": ["tests/test_openpi_live_service_smoke.py"],
                "capability_hint": "localhost live-service smoke",
                "change_kind": "validation",
            }
        ],
    )
    monkeypatch.setattr(
        MODULE,
        "_collect_gitlink_updates",
        lambda repo_root, commit_hash: [
            {
                "path": "src/mint",
                "old_sha": "old",
                "new_sha": "new",
                "status": "M",
            }
        ],
    )

    payload = MODULE.collect_daily_report_facts(Path.cwd(), "2026-03-12", start_commit="def456")

    assert any(
        command == "cd src/mint && .venv/bin/pytest tests/test_openpi_live_service_smoke.py -vv -ra"
        for command in payload["verification_commands"]
    )


def _init_git_repo(path: Path) -> str:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True, capture_output=True, text=True)
    (path / "tracked.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True, text=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.mark.parametrize(
    ("old_sha", "new_sha"),
    [
        ("HEAD", "0" * 39 + "1"),
        ("0" * 39 + "1", "HEAD"),
    ],
)
def test_collect_submodule_code_evidence_skips_missing_gitlink_objects(
    tmp_path: Path,
    old_sha: str,
    new_sha: str,
) -> None:
    repo_root = tmp_path / "repo-root"
    repo_root.mkdir()
    submodule_root = repo_root / "src" / "mint"
    submodule_root.mkdir(parents=True)
    head_sha = _init_git_repo(submodule_root)

    resolved_old = head_sha if old_sha == "HEAD" else old_sha
    resolved_new = head_sha if new_sha == "HEAD" else new_sha

    evidence = MODULE._collect_submodule_code_evidence(
        repo_root=repo_root,
        submodule_path="src/mint",
        old_sha=resolved_old,
        new_sha=resolved_new,
        subject="Update submodule",
        commit_hash="abc123",
        author_date="2026-03-13T10:00:00+08:00",
    )

    assert evidence == []
