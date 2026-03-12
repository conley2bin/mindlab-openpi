---
name: volcano-cluster
description: Use when inspecting or operating Mint's Volcano and Ray development cluster, especially for head or worker task state, head IP discovery, GPU worker allocation, explicit `RAY_ADDRESS`, or validating that `mint-dev` should connect to an existing cluster.
---

# Volcano Cluster

## Overview

This skill owns Mint dev cluster lifecycle and cluster discovery. It does not own local code sync and it does not own per-user namespace policy.

Use `mint-dev` after cluster state is known. Use `mint-sync-unison` for local-to-PFS sync. Use `ray-namespace-isolation` before creating new dev workers or attaching a server to a shared cluster.

## Current Dev Model

- `mint-dev` is a driver host.
- Ray head and GPU workers run as Volcano tasks.
- The server should connect to the active head with explicit `RAY_ADDRESS=<head_ip>:6379`.
- Do not infer cluster health from `mint-dev` local resources.
- On 2026-03-13 the active shared dev head reachable from `mint-dev` was `192.168.37.134:6379`.
- A stale address `192.168.37.7:6379` also existed. Do not reuse an address just because `address="auto"` found it once.
- `ray status` against `192.168.37.134:6379` showed an existing shared cluster with active GPU workers. Do not create a new cluster if this head is still alive.
- `ssh mint-dev` lands as `root`. Resolve the active PFS tree from `/root/tinker_project/tinker-server` instead of expanding remote `$USER`.

## Read-Only Cluster Discovery

If Volcano CLI works on your current host, list tasks there. Current reality can differ by host: `mint-dev` may fail `ml_task` because the `mlp` helper is missing, and the repo host may have no accessible `volc` at all. Use the Volcano console or another approved bastion where `/root/.volc/bin/volc ml_task list` actually succeeds.

Expected dev task names:

- `mint-dev-head`
- `mint-dev-worker*`

Head IP discovery from a host where `ml_task` works:

```bash
/root/.volc/bin/volc ml_task logs -t <head_task_id> -i worker_0 | grep "Local node IP"
```

Connectivity proof:

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

Ray attach check:

```bash
ssh mint-dev 'ROOT=/root/tinker_project/tinker-server; \
PFS_ROOT=$(readlink -f "$ROOT"); \
VENV="$PFS_ROOT/.venv31213"; \
RAY_ADDRESS=REPLACE_WITH_HEAD_IP:6379 \
"$VENV/bin/python3.12" - <<'"'"'PY'"'"'
import json
import ray
ray.init(address="auto")
print(json.dumps({
    "cluster_resources": ray.cluster_resources(),
    "available_resources": ray.available_resources(),
}))
PY'
```

If you need actor metadata from `mint-dev`, prefer `ray._private.state` or a head-pinned Ray task. `ray.util.state.*` from `mint-dev` can fail if it tries to reach a dashboard bound only to head-local `127.0.0.1:8265`.

## Templates

Use the root-level templates in this skill, not `src/mint/.claude/skills/*`:

- `references/mint-dev-head.yaml`
- `references/mint-dev-worker.yaml`

The worker template intentionally keeps these as placeholders:

- `<TASK_NAME>`
- `<RAY_HEAD_IP>`
- `<GPU_QUEUE_ID>`
- `<PFS_TINKER_PATH>`

Do not submit a worker template that still points to shared `/vePFS-Mindverse/share/code/tinker-server`.

## Create Or Refresh A Dev Cluster

1. Submit the head template.
2. Read head logs to obtain the live IP.
3. Copy the worker template to a temp file.
4. Fill in task name, head IP, GPU queue, and per-user PFS path.
5. Submit workers.
6. Verify `6379` connectivity and `ray.cluster_resources()` from `mint-dev`.

## Attach Mint Dev To An Existing Cluster

When reusing the shared cluster instead of creating a new one, the `mint-dev` host still needs its own local CPU-only raylet membership before host-local drivers and `run_server.py` behave reliably.

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

After attach, verify both cluster resources and GPU scheduling from `mint-dev`:

```bash
ssh mint-dev 'ROOT=/root/tinker_project/tinker-server; \
PFS_ROOT=$(readlink -f "$ROOT"); \
VENV="$PFS_ROOT/.venv31213"; \
RAY_ADDRESS=REPLACE_WITH_HEAD_IP:6379 \
TINKER_RAY_NAMESPACE=REPLACE_WITH_NAMESPACE \
"$VENV/bin/python3.12" - <<'"'"'PY'"'"'
import json
import os
import ray
ray.init(address="auto", namespace=os.environ["TINKER_RAY_NAMESPACE"], ignore_reinit_error=True)
@ray.remote(num_gpus=1)
def probe():
    import os, sys
    return {"python": sys.version.split()[0], "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}
print(json.dumps(ray.get(probe.remote()), ensure_ascii=False))
PY'
```

## Guardrails

- Do not use stale `address="auto"` results as cluster truth.
- Do not create workers against shared code roots.
- Do not attach `mint-dev` with Python 3.12.12 to the shared 3.12.13 cluster.
- Do not bind the local `mint-dev` raylet to `9.36.26.252`; that address failed GCS heartbeats.
- Do not assume the GPU queue is fixed. Confirm it before submit.
- Do not assume `mint-dev` itself is a usable Volcano bastion.
- Do not change namespaces or PFS paths without `ray-namespace-isolation`.
