from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_runner_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "tools" / "mint_dev_preflight.py"
    spec = importlib.util.spec_from_file_location("mint_dev_preflight", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_report(*, overall_state: str = "queue_healthy") -> dict[str, object]:
    return {
        "overall_state": overall_state,
        "ssh_host": "mint-dev",
        "base_url": "http://localhost:8000",
        "request_id": "req-123",
        "steps": [
            {"name": "host_identity", "status": "pass", "summary": "mint-dev root"},
            {"name": "server_root", "status": "pass", "summary": "/vePFS-Mindverse/share/code/conley/tinker-server"},
            {"name": "healthz", "status": "pass", "summary": "200 ready"},
            {"name": "debug_state", "status": "pass", "summary": "actor reachable"},
            {"name": "noop", "status": "pass", "summary": "request_id=req-123"},
            {"name": "retrieve_future", "status": "pass", "summary": "ok"},
        ],
    }


def test_plan_ssh_command_uses_defaults() -> None:
    runner = _load_runner_module()

    command = runner.plan_ssh_command(
        ssh_host="mint-dev",
        base_url="http://localhost:8000",
        server_root="/root/tinker_project/tinker-server",
        logfile="/tmp/tinker_server.log",
        log_lines=40,
        retrieve_timeout_s=5.0,
        poll_interval_s=0.2,
    )

    assert command[0] == "ssh"
    assert command[1:5] == ("-o", "BatchMode=yes", "-o", "ConnectTimeout=10")
    assert command[5] == "mint-dev"
    assert "python3 - <<'PY'" in command[6]
    assert "http://localhost:8000" in command[6]
    assert "/root/tinker_project/tinker-server" in command[6]
    assert "/tmp/tinker_server.log" in command[6]
    assert "scripts/run_server.py" in command[6]
    assert 'os.path.exists(resolved_root)' in command[6]
    assert "server root missing:" in command[6]
    assert "log read failed:" in command[6]


def test_plan_ssh_command_threads_api_key_to_all_queue_probes() -> None:
    runner = _load_runner_module()

    command = runner.plan_ssh_command(
        ssh_host="mint-dev",
        base_url="http://localhost:8000",
        server_root="/root/tinker_project/tinker-server",
        logfile="/tmp/tinker_server.log",
        log_lines=40,
        retrieve_timeout_s=5.0,
        poll_interval_s=0.2,
        api_key="sk-test",
    )

    assert 'headers["X-API-Key"] = CONFIG["api_key"]' in command[6]
    assert '"/internal/work_queue/debug_state"' in command[6]
    assert '"/internal/work_queue/noop"' in command[6]
    assert command[6].count("headers=headers") >= 4


def test_plan_ssh_command_requires_terminal_success_payload_for_retrieve_future() -> None:
    runner = _load_runner_module()

    command = runner.plan_ssh_command(
        ssh_host="mint-dev",
        base_url="http://localhost:8000",
        server_root="/root/tinker_project/tinker-server",
        logfile="/tmp/tinker_server.log",
        log_lines=40,
        retrieve_timeout_s=5.0,
        poll_interval_s=0.2,
    )

    assert 'future_data.get("ok") is True' in command[6]
    assert 'future_data.get("op") == "internal.noop"' in command[6]


def test_extract_report_from_ssh_output_uses_prefixed_json_line() -> None:
    runner = _load_runner_module()

    report = runner.extract_report_from_ssh_output(
        'login banner\nMINT_DEV_PREFLIGHT_REPORT={"overall_state":"queue_healthy","steps":[],"observations":[]}\n'
    )

    assert report["overall_state"] == "queue_healthy"
    assert report["observations"] == []


def test_extract_report_from_ssh_output_rejects_missing_prefixed_json_line() -> None:
    runner = _load_runner_module()

    with pytest.raises(ValueError, match="MINT_DEV_PREFLIGHT_REPORT"):
        runner.extract_report_from_ssh_output("login banner only\n")


@pytest.mark.parametrize(
    ("overall_state", "exit_code"),
    [
        ("queue_healthy", 0),
        ("ssh_failure", 10),
        ("server_unavailable", 20),
        ("queue_unhealthy", 30),
        ("runner_error", 40),
    ],
)
def test_determine_exit_code_maps_report_states(overall_state: str, exit_code: int) -> None:
    runner = _load_runner_module()

    report = _sample_report(overall_state=overall_state)

    assert runner.determine_exit_code(report) == exit_code


def test_render_text_report_includes_overall_state_and_key_steps() -> None:
    runner = _load_runner_module()

    text = runner.render_text_report(_sample_report())

    assert "overall_state: queue_healthy" in text
    assert "ssh_host: mint-dev" in text
    assert "healthz: pass 200 ready" in text
    assert "retrieve_future: pass ok" in text


def test_main_dry_run_prints_ssh_command(monkeypatch, capsys) -> None:
    runner = _load_runner_module()

    monkeypatch.setattr(
        runner.sys,
        "argv",
        ["mint_dev_preflight.py", "--dry-run"],
    )

    assert runner.main() == 0
    out = capsys.readouterr().out
    assert "ssh -o BatchMode=yes -o ConnectTimeout=10 mint-dev" in out
    assert "BatchMode=yes" in out
    assert "ConnectTimeout=10" in out
    assert "python3 - <<" in out
    assert "PY" in out


def test_main_json_output_reports_successful_non_dry_run(monkeypatch, capsys) -> None:
    runner = _load_runner_module()
    report = _sample_report()
    sentinel = runner.REPORT_PREFIX + json.dumps(report, sort_keys=True)

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=f"banner\n{sentinel}\n")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner.sys,
        "argv",
        ["mint_dev_preflight.py", "--json"],
    )

    assert runner.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_state"] == "queue_healthy"
    assert payload["exit_code"] == 0
    assert payload["request_id"] == "req-123"


def test_main_classifies_nonzero_remote_bootstrap_failure_as_ssh_failure(monkeypatch, capsys) -> None:
    runner = _load_runner_module()

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=7, stdout="python3: not found\n")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner.sys,
        "argv",
        ["mint_dev_preflight.py", "--json"],
    )

    assert runner.main() == 10
    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_state"] == "ssh_failure"
    assert payload["exit_code"] == 10
    assert "python3: not found" in payload["steps"][0]["summary"]


def test_main_classifies_missing_report_with_zero_exit_as_runner_error(monkeypatch, capsys) -> None:
    runner = _load_runner_module()

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="banner only\n")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner.sys,
        "argv",
        ["mint_dev_preflight.py", "--json"],
    )

    assert runner.main() == 40
    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_state"] == "runner_error"
    assert payload["exit_code"] == 40
    assert "malformed ssh output" in payload["steps"][0]["summary"]


def test_main_classifies_ssh_timeout_as_ssh_failure(monkeypatch, capsys) -> None:
    runner = _load_runner_module()

    def fake_run(*args, **kwargs):
        raise runner.subprocess.TimeoutExpired(args[0], timeout=30.0, output="ssh timed out")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner.sys,
        "argv",
        ["mint_dev_preflight.py", "--json"],
    )

    assert runner.main() == 10
    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_state"] == "ssh_failure"
    assert payload["exit_code"] == 10
    assert "timed out" in payload["steps"][0]["summary"]


def test_main_classifies_local_ssh_spawn_failure_as_ssh_failure(monkeypatch, capsys) -> None:
    runner = _load_runner_module()

    def fake_run(*args, **kwargs):
        raise OSError("ssh not found")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner.sys,
        "argv",
        ["mint_dev_preflight.py", "--json"],
    )

    assert runner.main() == 10
    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_state"] == "ssh_failure"
    assert payload["exit_code"] == 10
    assert "ssh exec failed" in payload["steps"][0]["summary"]
