---
name: mint-dev
description: Use when checking or operating the Mint development host on `ssh mint-dev`, especially for dev server health, logs, startup environment, explicit `RAY_ADDRESS`, or deciding whether a problem belongs to server startup, code sync, or Ray/Volcano state.
---

# Mint Dev

## Overview

`mint-dev` is the development driver host. It is not the source of truth for code sync and it may have no local GPU even when the dev cluster has active GPU workers.

Use this skill for host-local server work. Use `mint-sync-unison` for local-to-PFS sync. Use `volcano-cluster` for head/worker lifecycle. Use `ray-namespace-isolation` for namespace and per-user path decisions.

## Verified Facts

- SSH host: `ssh mint-dev`
- Default API port: `8000`
- Server log: `/tmp/tinker_server.log`
- Server working tree path: `/root/tinker_project/tinker-server`
- The server path is usually a symlink into per-user PFS, not a Git checkout.
- Current reachable shared head observed on 2026-03-13: `192.168.37.134:6379`.
- A stale head address `192.168.37.7:6379` also existed and timed out.
- `ray.init(address="auto")` can bind to a stale head. Prefer an explicit `RAY_ADDRESS` taken from the active dev head.
- `mint-dev` default `python3` is `3.12.12`, while the active shared Ray cluster is `Python 3.12.13`.
- Observed working runtime under the active symlink target on 2026-03-13: `/vePFS-Mindverse/share/code/conley/tinker-server/.python-3.12.13` and `/vePFS-Mindverse/share/code/conley/tinker-server/.venv31213`.
- `mint-dev` needs a local CPU-only raylet joined to the shared cluster before host-local drivers and `run_server.py` behave reliably. The stable node IP on 2026-03-13 was `192.168.33.174`; binding to `9.36.26.252` died from missed heartbeats.
- `mint-dev` itself may show no GPU in `nvidia-smi`. Do not treat that as proof that the Ray cluster has no GPU workers.
- `GET /api/v1/healthz -> 200 {"status":"ready"}` does not prove detached `tinker_api_work_queue` is healthy.

## Read-Only Triage

Run these first:

```bash
ssh mint-dev 'hostname; whoami'
ssh mint-dev 'readlink -f /root/tinker_project/tinker-server'
ssh mint-dev 'ps aux | grep run_server | grep -v grep || true'
ssh mint-dev 'tail -50 /tmp/tinker_server.log'
ssh mint-dev 'curl -sS -m 5 http://localhost:8000/api/v1/healthz'
ssh mint-dev 'curl -sS -m 10 http://localhost:8000/internal/work_queue/debug_state'
```

The health probe above runs on `mint-dev`. A local `curl http://localhost:8000/...` only makes sense after you create an explicit SSH tunnel.

Interpretation:

- `connection refused`: server is not running.
- `503` from `/api/v1/healthz`: server is up; Ray or capacity may be degraded.
- `200` from `/api/v1/healthz` with `500` on `/internal/work_queue/debug_state` or `503` on `/internal/work_queue/noop`: the HTTP process is up, but detached queue actor control-plane is not healthy.
- `Version mismatch: Ray ... Python ...`: the server interpreter does not match the active Ray cluster runtime.
- `Failed to connect to GCS`: treat `address="auto"` as suspect until you verify the current head IP.
- `Get timed out: some object(s) not ready.` from queue endpoints: check queue actor health before blaming generic HTTP transport.

## Discover The Active Ray Head

Do not trust `address="auto"` blindly.

1. Use `volcano-cluster` to identify the active dev head task.
2. Extract the current head IP from head task logs.
3. Prove port `6379` is reachable before starting or debugging the server.

```bash
ssh mint-dev 'python3 - <<'"'"'PY'"'"'
import socket, json
host = "REPLACE_WITH_HEAD_IP"
s = socket.socket()
s.settimeout(3)
try:
    s.connect((host, 6379))
    print(json.dumps({"host": host, "port": 6379, "connect": True}))
except Exception as exc:
    print(json.dumps({"host": host, "port": 6379, "connect": False, "error": str(exc)}))
finally:
    s.close()
PY'
```

## Ensure Local Raylet Membership

On `mint-dev`, host-local drivers and `run_server.py` must see a live local raylet joined to the shared head.

```bash
ssh mint-dev 'ROOT=/root/tinker_project/tinker-server; \
PFS_ROOT=$(readlink -f "$ROOT"); \
VENV="$PFS_ROOT/.venv31213"; \
"$VENV/bin/python3.12" -m ray.scripts.scripts start \
  --address=REPLACE_WITH_HEAD_IP:6379 \
  --node-ip-address=REPLACE_WITH_MINT_DEV_NODE_IP \
  --num-cpus=0 \
  --num-gpus=0 \
  --disable-usage-stats \
  --log-style=record'
```

Verify the joined local node from `mint-dev`:

```bash
ssh mint-dev 'ROOT=/root/tinker_project/tinker-server; \
PFS_ROOT=$(readlink -f "$ROOT"); \
VENV="$PFS_ROOT/.venv31213"; \
RAY_ADDRESS=REPLACE_WITH_HEAD_IP:6379 \
"$VENV/bin/python3.12" -m ray.scripts.scripts status'
```

## Start Or Restart The Dev Server

Never borrow another developer's private interpreter path. Verify which interpreter exists under your current PFS-backed tree first.

```bash
ssh mint-dev 'ROOT=/root/tinker_project/tinker-server; \
PFS_ROOT=$(readlink -f "$ROOT"); \
printf "%s\n" "PFS_ROOT=$PFS_ROOT"; \
for p in "$PFS_ROOT/.venv31213/bin/python3.12" "$PFS_ROOT/.python-3.12.13/bin/python3.12" "$ROOT/.venv/bin/python" python3; do \
  if [ "$p" = python3 ] || [ -x "$p" ]; then echo "$p"; break; fi; \
done'
```

Once you know:

- `RAY_ADDRESS`
- `PFS_TINKER_PATH`
- `TINKER_RAY_NAMESPACE`
- interpreter path

start the server with explicit values:

```bash
ssh mint-dev 'pkill -f "[r]un_server.py" 2>/dev/null || true'
ssh mint-dev 'ROOT=/root/tinker_project/tinker-server; \
PFS_ROOT=$(readlink -f "$ROOT"); \
cd "$ROOT" && nohup bash -c "
  PYTHONPATH=$ROOT:\$PYTHONPATH \
  HF_HUB_OFFLINE=1 HF_HOME=/vePFS-Mindverse/share/huggingface \
  PYTHONDONTWRITEBYTECODE=1 \
  RAY_ADDRESS=REPLACE_WITH_HEAD_IP:6379 \
  PFS_TINKER_PATH=$PFS_ROOT \
  TINKER_RAY_NAMESPACE=REPLACE_WITH_NAMESPACE \
  MINT_RAY_NAMESPACE=REPLACE_WITH_NAMESPACE \
  REPLACE_WITH_INTERPRETER scripts/run_server.py
" >> /tmp/tinker_server.log 2>&1 &'
```

## Validate The Queue Control Plane

Do not stop at `/api/v1/healthz`.

```bash
ssh mint-dev 'curl -sS -m 5 http://localhost:8000/api/v1/healthz'
ssh mint-dev 'curl -sS -m 10 http://localhost:8000/internal/work_queue/debug_state'
ssh mint-dev 'curl -sS -m 10 -X POST http://localhost:8000/internal/work_queue/noop'
ssh mint-dev 'curl -sS -m 10 -X POST http://localhost:8000/api/v1/retrieve_future \
  -H "content-type: application/json" \
  -d "{\"request_id\":\"REPLACE_WITH_NOOP_REQUEST_ID\"}"'
```

Healthy flow:

- `/api/v1/healthz` returns `200`
- `/internal/work_queue/debug_state` returns queue stats JSON
- `/internal/work_queue/noop` returns a `request_id`
- `/api/v1/retrieve_future` returns `{"ok": true, "op": "internal.noop", ...}`

## Recycle A Bad Queue Actor

If `healthz` is ready but queue control-plane probes fail, recycle only the queue actor in the active namespace, then restart the server.

```bash
ssh mint-dev 'ROOT=/root/tinker_project/tinker-server; \
PFS_ROOT=$(readlink -f "$ROOT"); \
VENV="$PFS_ROOT/.venv31213"; \
RAY_ADDRESS=REPLACE_WITH_HEAD_IP:6379 \
TINKER_RAY_NAMESPACE=REPLACE_WITH_NAMESPACE \
"$VENV/bin/python3.12" - <<'"'"'PY'"'"'
import os
import ray
ray.init(address="auto", namespace=os.environ["TINKER_RAY_NAMESPACE"], ignore_reinit_error=True)
actor = ray.get_actor("tinker_api_work_queue", namespace=os.environ["TINKER_RAY_NAMESPACE"])
ray.kill(actor, no_restart=True)
PY'
```

## Guardrails

- Do not assume `mint-dev` has a usable local GPU.
- Do not assume `/root/tinker_project/tinker-server` contains `.git`.
- Do not start the server with `address="auto"` when a stale head address is plausible.
- Do not start host-local drivers with `python3` 3.12.12 against the shared 3.12.13 cluster.
- Do not skip the local raylet join check on `mint-dev`.
- Do not treat `healthz ready` as proof that `api_work_queue` is healthy.
- Do not point `PFS_TINKER_PATH` at another developer's tree.
- Do not pick a namespace until `ray-namespace-isolation` rules are satisfied.
