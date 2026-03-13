#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import textwrap
from typing import Any, Sequence


REPORT_PREFIX = "MINT_DEV_PREFLIGHT_REPORT="

DEFAULT_SSH_HOST = "mint-dev"
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_SERVER_ROOT = "/root/tinker_project/tinker-server"
DEFAULT_LOGFILE = "/tmp/tinker_server.log"
DEFAULT_LOG_LINES = 40
DEFAULT_RETRIEVE_TIMEOUT_S = 5.0
DEFAULT_POLL_INTERVAL_S = 0.2
DEFAULT_SSH_CONNECT_TIMEOUT_S = 10
DEFAULT_SSH_COMMAND_TIMEOUT_S = 30.0

EXIT_CODES = {
    "queue_healthy": 0,
    "ssh_failure": 10,
    "server_unavailable": 20,
    "queue_unhealthy": 30,
    "runner_error": 40,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a repo-owned preflight check against ssh mint-dev and validate the queue control-plane."
    )
    parser.add_argument("--ssh-host", default=DEFAULT_SSH_HOST)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--server-root", default=DEFAULT_SERVER_ROOT)
    parser.add_argument("--logfile", default=DEFAULT_LOGFILE)
    parser.add_argument("--log-lines", type=int, default=DEFAULT_LOG_LINES)
    parser.add_argument("--retrieve-timeout-s", type=float, default=DEFAULT_RETRIEVE_TIMEOUT_S)
    parser.add_argument("--poll-interval-s", type=float, default=DEFAULT_POLL_INTERVAL_S)
    parser.add_argument("--ssh-connect-timeout-s", type=int, default=DEFAULT_SSH_CONNECT_TIMEOUT_S)
    parser.add_argument("--ssh-command-timeout-s", type=float, default=DEFAULT_SSH_COMMAND_TIMEOUT_S)
    parser.add_argument("--api-key")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _remote_probe_script(
    *,
    base_url: str,
    server_root: str,
    logfile: str,
    log_lines: int,
    retrieve_timeout_s: float,
    poll_interval_s: float,
    api_key: str | None,
) -> str:
    config = {
        "base_url": base_url.rstrip("/"),
        "server_root": server_root,
        "logfile": logfile,
        "log_lines": int(log_lines),
        "retrieve_timeout_s": float(retrieve_timeout_s),
        "poll_interval_s": float(poll_interval_s),
        "api_key": api_key,
    }
    return textwrap.dedent(
        f"""\
        python3 - <<'PY'
        import collections
        import getpass
        import json
        import os
        import subprocess
        import sys
        import time
        import urllib.error
        import urllib.request

        CONFIG = json.loads({json.dumps(config)!r})
        REPORT_PREFIX = {REPORT_PREFIX!r}

        def step(name, status, summary, **details):
            item = {{"name": name, "status": status, "summary": summary}}
            if details:
                item["details"] = details
            return item

        def read_tail(path, limit):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    return list(collections.deque(handle, maxlen=limit)), None
            except FileNotFoundError:
                return None, None
            except OSError as exc:
                return None, f"{{type(exc).__name__}}: {{exc}}"

        def http_json(method, path, *, payload=None, timeout=5.0, headers=None):
            body = None
            req_headers = {{"content-type": "application/json"}}
            if headers:
                req_headers.update(headers)
            if payload is not None:
                body = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                CONFIG["base_url"] + path,
                data=body,
                method=method,
                headers=req_headers,
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    raw = response.read().decode("utf-8", errors="replace")
                    status = int(response.status)
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8", errors="replace")
                status = int(exc.code)
            data = None
            if raw:
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = None
            return status, raw, data

        report = {{
            "overall_state": "runner_error",
            "base_url": CONFIG["base_url"],
            "server_root_input": CONFIG["server_root"],
            "logfile": CONFIG["logfile"],
            "observations": [],
            "steps": [],
        }}

        host = os.environ.get("HOSTNAME") or ""
        try:
            if not host:
                host = subprocess.run(
                    ["hostname"],
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                ).stdout.strip()
        except Exception:
            host = ""
        report["ssh_host"] = host or "unknown"

        whoami = getpass.getuser()
        report["steps"].append(step("host_identity", "pass", f"{{host or 'unknown'}} {{whoami}}"))

        resolved_root = os.path.realpath(CONFIG["server_root"])
        if os.path.exists(resolved_root):
            report["steps"].append(step("server_root", "pass", resolved_root))
        else:
            report["observations"].append(
                f"server root missing: {{CONFIG['server_root']}} -> {{resolved_root}}"
            )
            report["steps"].append(
                step(
                    "server_root",
                    "fail",
                    f"missing {{resolved_root}}",
                    input_path=CONFIG["server_root"],
                    resolved_path=resolved_root,
                )
            )

        ps_run = subprocess.run(
            ["ps", "-ef"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        matches = [
            line.strip()
            for line in ps_run.stdout.splitlines()
            if "scripts/run_server.py" in line
            and "python3 - <<'PY'" not in line
        ]
        if matches:
            report["steps"].append(
                step(
                    "server_process",
                    "pass",
                    f"observed {{len(matches)}} run_server.py process(es)",
                    matches=matches[:5],
                )
            )
        else:
            report["observations"].append("no run_server.py process observed")
            report["steps"].append(step("server_process", "fail", "no run_server.py process observed"))

        tail_lines, tail_error = read_tail(CONFIG["logfile"], CONFIG["log_lines"])
        if tail_error is not None:
            report["observations"].append(f"log read failed: {{CONFIG['logfile']}}: {{tail_error}}")
            report["steps"].append(
                step(
                    "server_log_tail",
                    "warn",
                    f"log read failed for {{CONFIG['logfile']}}",
                    error=tail_error,
                )
            )
        elif tail_lines is None:
            report["observations"].append(f"missing log file: {{CONFIG['logfile']}}")
            report["steps"].append(step("server_log_tail", "warn", f"missing {{CONFIG['logfile']}}"))
        else:
            report["steps"].append(
                step(
                    "server_log_tail",
                    "pass",
                    f"captured {{len(tail_lines)}} log line(s)",
                    tail="".join(tail_lines),
                )
            )

        headers = {{}}
        if CONFIG.get("api_key"):
            headers["X-API-Key"] = CONFIG["api_key"]

        try:
            health_status, health_raw, health_data = http_json("GET", "/api/v1/healthz", timeout=5.0, headers=headers)
        except Exception as exc:
            report["steps"].append(step("healthz", "fail", f"transport error: {{type(exc).__name__}}: {{exc}}"))
            report["overall_state"] = "server_unavailable"
            print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
            raise SystemExit(20)

        if health_status != 200 or not isinstance(health_data, dict):
            report["steps"].append(
                step(
                    "healthz",
                    "fail",
                    f"status={{health_status}} body={{health_raw[:200]!r}}",
                    http_status=health_status,
                )
            )
            report["overall_state"] = "server_unavailable"
            print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
            raise SystemExit(20)

        report["steps"].append(
            step(
                "healthz",
                "pass",
                f"{{health_status}} {{health_data.get('status', 'unknown')}}",
                http_status=health_status,
                payload=health_data,
            )
        )

        try:
            debug_status, debug_raw, debug_data = http_json(
                "GET",
                "/internal/work_queue/debug_state",
                timeout=10.0,
                headers=headers,
            )
        except Exception as exc:
            report["steps"].append(step("debug_state", "fail", f"transport error: {{type(exc).__name__}}: {{exc}}"))
            report["overall_state"] = "queue_unhealthy"
            print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
            raise SystemExit(30)

        if debug_status != 200 or not isinstance(debug_data, dict):
            report["steps"].append(
                step(
                    "debug_state",
                    "fail",
                    f"status={{debug_status}} body={{debug_raw[:200]!r}}",
                    http_status=debug_status,
                )
            )
            report["overall_state"] = "queue_unhealthy"
            print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
            raise SystemExit(30)

        report["steps"].append(
            step(
                "debug_state",
                "pass",
                "actor reachable",
                http_status=debug_status,
                keys=sorted(debug_data.keys()),
            )
        )

        try:
            noop_status, noop_raw, noop_data = http_json(
                "POST",
                "/internal/work_queue/noop",
                timeout=10.0,
                headers=headers,
            )
        except Exception as exc:
            report["steps"].append(step("noop", "fail", f"transport error: {{type(exc).__name__}}: {{exc}}"))
            report["overall_state"] = "queue_unhealthy"
            print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
            raise SystemExit(30)

        request_id = noop_data.get("request_id") if isinstance(noop_data, dict) else None
        if noop_status != 200 or not isinstance(request_id, str) or not request_id:
            report["steps"].append(
                step(
                    "noop",
                    "fail",
                    f"status={{noop_status}} body={{noop_raw[:200]!r}}",
                    http_status=noop_status,
                )
            )
            report["overall_state"] = "queue_unhealthy"
            print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
            raise SystemExit(30)

        report["request_id"] = request_id
        report["steps"].append(
            step(
                "noop",
                "pass",
                f"request_id={{request_id}}",
                http_status=noop_status,
            )
        )

        deadline = time.time() + float(CONFIG["retrieve_timeout_s"])
        last_status = None
        last_raw = None
        while time.time() < deadline:
            try:
                future_status, future_raw, future_data = http_json(
                    "POST",
                    "/api/v1/retrieve_future",
                    payload={{"request_id": request_id}},
                    timeout=10.0,
                    headers=headers,
                )
            except Exception as exc:
                report["steps"].append(
                    step("retrieve_future", "fail", f"transport error: {{type(exc).__name__}}: {{exc}}")
                )
                report["overall_state"] = "queue_unhealthy"
                print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
                raise SystemExit(30)

            last_status = future_status
            last_raw = future_raw
            if future_status == 408:
                time.sleep(float(CONFIG["poll_interval_s"]))
                continue
            if (
                future_status == 200
                and isinstance(future_data, dict)
                and future_data.get("ok") is True
                and future_data.get("op") == "internal.noop"
            ):
                report["steps"].append(
                    step(
                        "retrieve_future",
                        "pass",
                        "ok",
                        http_status=future_status,
                        payload=future_data,
                    )
                )
                report["overall_state"] = "queue_healthy"
                print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
                raise SystemExit(0)

            report["steps"].append(
                step(
                    "retrieve_future",
                    "fail",
                    f"status={{future_status}} body={{future_raw[:200]!r}}",
                    http_status=future_status,
                )
            )
            report["overall_state"] = "queue_unhealthy"
            print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
            raise SystemExit(30)

        report["steps"].append(
            step(
                "retrieve_future",
                "fail",
                f"timeout waiting for terminal noop result; last_status={{last_status}} body={{(last_raw or '')[:200]!r}}",
            )
        )
        report["overall_state"] = "queue_unhealthy"
        print(REPORT_PREFIX + json.dumps(report, sort_keys=True))
        raise SystemExit(30)
        PY"""
    )


def plan_ssh_command(
    *,
    ssh_host: str,
    base_url: str,
    server_root: str,
    logfile: str,
    log_lines: int,
    retrieve_timeout_s: float,
    poll_interval_s: float,
    ssh_connect_timeout_s: int = DEFAULT_SSH_CONNECT_TIMEOUT_S,
    api_key: str | None = None,
) -> tuple[str, ...]:
    remote_command = _remote_probe_script(
        base_url=base_url,
        server_root=server_root,
        logfile=logfile,
        log_lines=log_lines,
        retrieve_timeout_s=retrieve_timeout_s,
        poll_interval_s=poll_interval_s,
        api_key=api_key,
    )
    return (
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={int(ssh_connect_timeout_s)}",
        ssh_host,
        remote_command,
    )


def extract_report_from_ssh_output(output: str) -> dict[str, Any]:
    for line in reversed(output.splitlines()):
        if not line.startswith(REPORT_PREFIX):
            continue
        payload = line[len(REPORT_PREFIX) :]
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError(f"{REPORT_PREFIX} payload must decode to an object")
        return data
    raise ValueError(f"missing {REPORT_PREFIX} line in ssh output")


def determine_exit_code(report: dict[str, Any]) -> int:
    state = report.get("overall_state")
    if not isinstance(state, str):
        return EXIT_CODES["runner_error"]
    return EXIT_CODES.get(state, EXIT_CODES["runner_error"])


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"overall_state: {report.get('overall_state', 'unknown')}",
        f"ssh_host: {report.get('ssh_host', 'unknown')}",
        f"base_url: {report.get('base_url', 'unknown')}",
    ]
    if isinstance(report.get("request_id"), str):
        lines.append(f"request_id: {report['request_id']}")
    steps = report.get("steps")
    if isinstance(steps, list):
        for step in steps:
            if not isinstance(step, dict):
                continue
            name = step.get("name", "unknown")
            status = step.get("status", "unknown")
            summary = step.get("summary", "")
            lines.append(f"{name}: {status} {summary}".rstrip())
    return "\n".join(lines)


def _format_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _coerce_process_output(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return ""


def _synthetic_report(
    *,
    overall_state: str,
    ssh_host: str,
    base_url: str,
    summary: str,
) -> dict[str, Any]:
    return {
        "overall_state": overall_state,
        "ssh_host": ssh_host,
        "base_url": base_url,
        "observations": [],
        "steps": [
            {
                "name": "ssh",
                "status": "fail",
                "summary": summary,
            }
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    command = plan_ssh_command(
        ssh_host=args.ssh_host,
        base_url=args.base_url,
        server_root=args.server_root,
        logfile=args.logfile,
        log_lines=args.log_lines,
        retrieve_timeout_s=args.retrieve_timeout_s,
        poll_interval_s=args.poll_interval_s,
        ssh_connect_timeout_s=args.ssh_connect_timeout_s,
        api_key=args.api_key,
    )

    if args.dry_run:
        print(_format_command(command))
        return 0

    report: dict[str, Any] | None = None
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=float(args.ssh_command_timeout_s),
        )
    except subprocess.TimeoutExpired as exc:
        output = _coerce_process_output(getattr(exc, "stdout", None) or getattr(exc, "output", None))
        report = _synthetic_report(
            overall_state="ssh_failure",
            ssh_host=args.ssh_host,
            base_url=args.base_url,
            summary=(
                f"ssh timed out after {float(args.ssh_command_timeout_s):g}s"
                + (f": {output.strip()}" if output.strip() else "")
            ),
        )
    except OSError as exc:
        report = _synthetic_report(
            overall_state="ssh_failure",
            ssh_host=args.ssh_host,
            base_url=args.base_url,
            summary=f"ssh exec failed: {type(exc).__name__}: {exc}",
        )

    if report is None:
        stdout = _coerce_process_output(completed.stdout)
        try:
            report = extract_report_from_ssh_output(stdout)
        except (ValueError, json.JSONDecodeError) as exc:
            if completed.returncode != 0:
                summary = stdout.strip() or str(exc)
                report = _synthetic_report(
                    overall_state="ssh_failure",
                    ssh_host=args.ssh_host,
                    base_url=args.base_url,
                    summary=f"remote preflight failed with exit {completed.returncode}: {summary}",
                )
            else:
                report = _synthetic_report(
                    overall_state="runner_error",
                    ssh_host=args.ssh_host,
                    base_url=args.base_url,
                    summary=f"malformed ssh output: {stdout.strip() or exc}",
                )

    report.setdefault("ssh_host", args.ssh_host)
    report.setdefault("base_url", args.base_url)
    report.setdefault("observations", [])
    report["exit_code"] = determine_exit_code(report)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(render_text_report(report))

    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
