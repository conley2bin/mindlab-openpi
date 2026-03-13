# OpenPI Validation Baseline

Baseline date: 2026-03-13

## Current Hard Gates

### `src/openpi`

```bash
cd src/openpi && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest scripts/train_adapter_test.py -q
cd src/openpi && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES='' uv run pytest scripts/train_test.py -q -s
cd src/openpi && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES='' uv run pytest \
  src/openpi/training/config_test.py \
  src/openpi/integration/runtime_test.py \
  src/openpi/integration/artifacts_test.py \
  src/openpi/integration/training_test.py \
  scripts/serve_policy_test.py \
  src/openpi/models/lora_test.py -q
```

What these gates cover:

- local LoRA model surface
- debug config guardrails in `src/openpi/training/config.py`
- training script adapters delegating into `openpi.integration.training`
- local JAX training smoke with `debug` config and resume path
- deterministic inference facade contract
- deterministic artifact path and norm stats contract
- deterministic training facade contract
- websocket serving script adapter contract

What these gates do not cover:

- full PyTorch backend execution
- real checkpoint model creation / inference
- cross-repo contract
### `src/mint`

```bash
cd src/mint && .venv/bin/pytest \
  tests/test_issue_136_config_file_validation.py \
  tests/test_issue_18_checkpoint_tiering.py \
  tests/test_model_registry_env_config.py \
  tests/test_gateway_multi_target_routing.py \
  tests/test_client_compat_user_agent.py \
  tests/test_issue_190_checkpoint_archive_auth_signed_url.py \
  tests/test_issue_218_gateway_checkpoint_proxy.py \
  tests/tests_mock_api_work_queue_scheduler.py \
  tests/test_issue_281_scheduler_and_healthz.py \
  tests/test_tinker_prompt_logprobs_semantics.py \
  tests/test_openpi_app_registration.py \
  tests/test_openpi_config_validation.py \
  tests/test_openpi_service_contract.py \
  tests/test_openpi_does_not_pollute_tinker_types.py \
  tests/test_openpi_runtime_bridge.py \
  tests/test_openpi_artifact_proxy.py \
  tests/test_openpi_training_contract.py \
  tests/test_openpi_sft_training_contract.py -q
```

What these gates cover:

- config file validation
- model registry env overrides
- gateway multi-target routing behavior
- client user-agent compatibility logic
- checkpoint URI resolution, persistent-cache materialization and SFT alias round-trip back into the underlying OpenPI checkpoint tree
- checkpoint archive auth and checkpoint proxy regressions around existing paths
- detached `api_work_queue` scheduler semantics, stale dequeue wake-up on `active_job_id` change, and control-plane concurrency headroom above worker count
- healthz and route labeling behavior
- prompt logprobs semantics for the Tinker-compatible path
- OpenPI config gate and app registration behavior
- OpenPI schema isolation from token-only types
- OpenPI inference runtime bridge and HTTP status mapping
- OpenPI response-side negotiated capability header on status and infer routes
- OpenPI artifact resolve/archive contract and checkpoint reference restrictions
- OpenPI generic training start async envelope, FutureStore queueing semantics and Mint-owned run/checkpoint URI mapping
- OpenPI isolated SFT start async envelope, whitelisted `TrainConfig` override mapping, fail-fast rejection of unknown top-level request fields, and Mint-owned SFT run/checkpoint URI mapping

What these gates do not cover:

- live Ray-backed FutureStore behavior under a real OpenPI training workload
- toolkit namespace / SDK contract
- deterministic cross-repo closed loop

### `src/mindlab-toolkit`

```bash
cd src/mindlab-toolkit && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run --with pytest python -m pytest \
  tests/test_namespace_contract.py \
  tests/test_mint_polling_patch.py \
  tests/test_openpi_namespace_contract.py \
  tests/test_openpi_sdk_contract.py -q
```

What these gates cover:

- current top-level namespace contract
- current patch side effects for the Tinker-compatible layer
- explicit `mint.openpi.*` namespace contract
- OpenPI SDK config, distinct client identity, Mint OpenPI request envelopes, current Mint status payload decoding and generic/SFT future payload mapping
- fail-fast on mismatched negotiated capability header while keeping header-missing services compatible

What these gates do not cover:

- live Mint OpenPI deployment behavior
- real FutureStore polling against a running Mint service
- deterministic cross-repo closed loop

### Cross-repo deterministic lane

```bash
cd src/mint && .venv/bin/pytest \
  tests/test_openpi_cross_repo_closed_loop.py -q
```

What this gate covers:

- Mint OpenPI public status contract as consumed by Toolkit SDK
- Toolkit SDK to Mint OpenPI service to fake OpenPI runtime closed loop
- Toolkit SDK to Mint OpenPI artifact resolve and archive download closed loop
- Toolkit SDK to Mint OpenPI generic training start, isolated SFT start and generic `retrieve_future` closed loop
- current negotiated capability match path across Mint OpenPI routes as consumed by Toolkit SDK
- structured observation/action payload across repo boundaries
- Mint-owned artifact resolve summary and archive transport contract
- Mint-owned async generic training and SFT future pending / failure / success envelope and typed result decode
- lifecycle signal propagation via `reset_before_infer`

What this gate does not cover:

- real checkpoint model loading
- live deployment networking
- real-asset artifact end-to-end round-trips

### Cross-repo localhost live-service smoke

```bash
cd src/mint && .venv/bin/pytest \
  tests/test_openpi_live_service_smoke.py -q
```

What this gate covers:

- Toolkit SDK to Mint OpenPI service over real localhost TCP transport
- public status and inference over actual HTTP instead of in-process ASGI transport
- artifact resolve plus archive download over actual HTTP
- service-hosted checkpoint reference resolution, persistent-cache materialization and local checkpoint-layout tar.gz round-trip
- generic training start plus retrieve_future over actual HTTP, including background task scheduling
- isolated SFT training start plus retrieve_future over actual HTTP, including background task scheduling
- current negotiated capability match path over live HTTP for Mint OpenPI routes

What this gate does not cover:

- real checkpoint model loading
- deployed-service networking outside localhost
- remote asset download or manual real-checkpoint inference

### Cross-repo remote deployment smoke

Repo-owned runner:

```bash
cd src/mint && \
  python scripts/tools/openpi_remote_smoke.py \
    --base-url https://<deployment-host>
```

Underlying pytest lane:

```bash
cd src/mint && \
  MINT_OPENPI_REMOTE_SMOKE=1 \
  MINT_OPENPI_REMOTE_BASE_URL=https://<deployment-host> \
  MINT_OPENPI_REMOTE_OBSERVATION_PATH=$PWD/tests/fixtures/openpi_remote_observation.sample.json \
  .venv/bin/pytest tests/test_openpi_remote_deployment_smoke.py -q
```

Optional env for deeper coverage:

- `MINT_OPENPI_REMOTE_API_KEY`
- `MINT_OPENPI_REMOTE_TIMEOUT_S`
- `MINT_OPENPI_REMOTE_CHECKPOINT_URI`
- `MINT_OPENPI_REMOTE_CONFIG_NAME`
- `MINT_OPENPI_REMOTE_OBSERVATION_JSON`
- `MINT_OPENPI_REMOTE_OBSERVATION_PATH`

`src/mint/scripts/tools/openpi_remote_smoke.py` 默认驱动这条 lane，并把 sample fixture 模板解析成绝对路径 env。底层 pytest lane 仍然是 `tests/test_openpi_remote_deployment_smoke.py`。

如果要通过 runner 触发 real-checkpoint infer lane，需要再提供 `--checkpoint-uri ... --config-name ... --observation-sample`，或者用 `--observation-json` / `--observation-path` 取代 sample 模板。

`MINT_OPENPI_REMOTE_OBSERVATION_JSON` 与 `MINT_OPENPI_REMOTE_OBSERVATION_PATH` 二选一。仓库内置的是 sample fixture template：`src/mint/tests/fixtures/openpi_remote_observation.sample.json`。

What this lane covers:

- Toolkit SDK to deployed Mint OpenPI service outside localhost
- public status as the minimum remote deployment reachability signal
- artifact resolve and archive download when `MINT_OPENPI_REMOTE_CHECKPOINT_URI` is provided
- service-hosted real-checkpoint infer when `MINT_OPENPI_REMOTE_CHECKPOINT_URI`、`MINT_OPENPI_REMOTE_CONFIG_NAME` and one of `MINT_OPENPI_REMOTE_OBSERVATION_JSON` / `MINT_OPENPI_REMOTE_OBSERVATION_PATH` are provided
- explicit failure bucket prefixes in test failures: `environment`, `deployment`, `runtime`, `service`, `sdk`
- once `MINT_OPENPI_REMOTE_SMOKE=1`, missing or non-absolute `MINT_OPENPI_REMOTE_BASE_URL` and malformed / non-finite `MINT_OPENPI_REMOTE_TIMEOUT_S` are treated as `environment` failures; once the real-checkpoint infer lane is selected, malformed / non-object `MINT_OPENPI_REMOTE_OBSERVATION_JSON`, malformed / missing / non-absolute `MINT_OPENPI_REMOTE_OBSERVATION_PATH`, and setting both observation envs at once are also treated as `environment` failures. If neither observation env is provided, the infer lane is skipped instead of failing

What this lane does not cover:

- deterministic regression proof
- deployment-owned secret provisioning or base URL discovery
- promotion to hard gate without a stable environment owner

### Root `mint-dev` preflight gate

```bash
python3 scripts/tools/mint_dev_preflight.py --json
```

What this gate covers:

- repo-owned `ssh mint-dev` entry for generic service control-plane validation
- host identity, server root symlink target, `run_server.py` process observation and log tail capture
- local `GET /api/v1/healthz`
- local `GET /internal/work_queue/debug_state`
- local `POST /internal/work_queue/noop`
- local `POST /api/v1/retrieve_future` polling until the noop request reaches a terminal result

What this gate does not cover:

- remote deployment owner or remote base URL discovery
- OpenPI-specific `/api/v1/openpi/*` semantics
- server restart, actor recycle, raylet attach or other remediation
- real-checkpoint infer or artifact validation

Latest observed report on 2026-03-13:

- `overall_state=queue_healthy`
- remote host identity observed as `di-20260204195152-27xws root`
- `/root/tinker_project/tinker-server` resolved to `/vePFS-Mindverse/share/code/conley/tinker-server`
- one `scripts/run_server.py` process was observed
- `healthz` / `debug_state` / `noop` / `retrieve_future` all passed

### Historical Mint Dev Observations To Re-Verify

Only the root `mint-dev` preflight gate above is current verification for this slice. The bullets below include earlier manual-debug observations and mutating remediation context. Re-verify current head IP, runtime path, node IP, restart behavior and actor identity before acting on shared infrastructure.

- `mint-dev` 是 dev driver host，不是 GPU worker 的同义词；`nvidia-smi` 无本地 GPU 不能推出 Ray dev cluster 无 GPU worker。
- `mint-dev` 上 server liveness 需要单独检查，不能从 cluster 状态反推。2026-03-13 的手工调试里同时观测到过 `curl http://localhost:8000/api/v1/healthz` 的 `connection refused`，也观测到过 restart 后的 `200 {"status":"ready"}`；后续判断必须直接探测当前 server 进程和 HTTP 结果。
- `ray.init(address="auto")` 在 `mint-dev` 上可能指向 stale head。2026-03-13 的手工调试里曾同时观测到一个不可达旧地址 `192.168.37.7:6379` 与一个可达显式 head 地址 `192.168.37.134:6379`；后续运维动作必须先验证当前活跃 head，再设 `RAY_ADDRESS=<head_ip>:6379`。
- `mint-dev` 默认 `python3` 是 `3.12.12`，与 2026-03-13 手工调试时看到的 shared Ray cluster `Python 3.12.13` 不匹配；当日可用的 conley-owned runtime 在 `/vePFS-Mindverse/share/code/conley/tinker-server/.python-3.12.13` 与 `/vePFS-Mindverse/share/code/conley/tinker-server/.venv31213`。
- 2026-03-13 的 shared-cluster 手工调试里，host-local driver 和 `run_server.py` 在本地 CPU-only raylet 加入 shared head 后才稳定；当日验证通过的本地 node IP 是 `192.168.33.174`，而 `9.36.26.252` 会因为 missed heartbeats 被 GCS 判死。
- 当前 `volc ml_task` 入口不统一：`mint-dev` 上 `ml_task` 会因为缺失 `mlp` helper 失败，本地 repo host 也没有可直接使用的 `volc`；cluster discovery 目前需要 Volcano console 或另一个已配置 CLI host。
- code sync 的主动端在本机 Unison daemon，不在 `mint-dev`。`/root/tinker_project/tinker-server` 通常是指向 per-user PFS tree 的 symlink，远端 PFS tree 没有 `.git` 属于预期；`ssh mint-dev` 登陆用户是 `root`，远端 `$USER` 不能作为 PFS owner 的判断依据。
- `GET /api/v1/healthz -> 200 {"status":"ready"}` 不能证明 detached `tinker_api_work_queue` healthy；当前最短验证链是 `/api/v1/healthz`、`/internal/work_queue/debug_state`、`/internal/work_queue/noop` 和 `/api/v1/retrieve_future`。
- 主仓库 `scripts/tools/mint_dev_preflight.py` 现在把这条 generic queue control-plane 验证链固化成 repo-owned CLI；默认不做 restart 或 actor recycle，但会发一个 `internal.noop` request 作为最小 control-plane probe。
- 当前 `tinker_server.backend.api_work_queue` 的代码约束是：detached actor 的 control-plane concurrency 必须高于 `api_work_queue_num_workers`，`active_job_id` 变更时要唤醒 stale `dequeue` waiters，而且 `_get_or_create_ray_actor()` 只会复用 `stats().protocol_version` 与当前代码一致的 named actor。
- 2026-03-13 在 `mint-dev` 上的手工调试里，旧 detached actor `c0f9c6115f011ddbdc48ef10bc030000` 在第一次 server-only restart 时被自动回收并替换成新 actor `1be8226feb5c80fb7c29a5aeda030000`；随后连续两次只重启 server，actor id 保持不变，`active_job_id` 从 `de030000` 继续推进到 `e1030000`，`healthz`、`debug_state`、`noop` 和 `retrieve_future` 持续通过。这是历史观察，不是当前 hard gate。
- 主仓库 `.codex/skills/{mint-dev,volcano-cluster,mint-sync-unison,ray-namespace-isolation}` 现在作为这组运维约束的 canonical agent entry；`src/mint/.claude/skills/*` 继续保留参考价值，但不再是主仓库工作流唯一入口。

## Real-Asset Exploratory Lane

```bash
cd src/openpi && uv run pytest --strict-markers -m "manual" src/openpi/policies/policy_test.py -q
cd src/openpi && uv run pytest src/openpi/shared/download_test.py -q
```

What this lane covers:

- `pi0_aloha_sim` real checkpoint policy creation and inference semantics
- remote asset download and checkpoint materialization paths inside `src/openpi`

What this lane requires:

- external network access
- enough device memory for real checkpoint load
- explicit acceptance of `manual` coverage

How to read failures:

- download failure or asset lookup failure: environment or remote asset problem first
- model init `RESOURCE_EXHAUSTED`: environment capacity problem first
- payload shape drift after model load: likely `src/openpi` runtime regression
- service or SDK mismatch after a successful real checkpoint load: outside this lane; escalate to `src/mint` or `src/mindlab-toolkit`

## Current Weak Lanes

These are useful, but they are not hard gates for the first implementation pass.

| Repo | Weak lane | Why weak |
| --- | --- | --- |
| `src/openpi` | `src/openpi/src/openpi/models/model_test.py` | 当前在本机 GPU 上 OOM；失败停在模型初始化阶段，不是 integration facade regression proof |
| `src/openpi` | `src/openpi/src/openpi/policies/policy_test.py` | marked `manual`; depends on real checkpoint download and actual inference |
| `src/openpi` | `src/openpi/src/openpi/shared/download_test.py` | depends on remote assets |
| cross-repo | any future real checkpoint closed loop | not deterministic; mixes contract problems with resource/network problems |

## Missing Validation Layers

| Layer | Current state |
| --- | --- |
| OpenPI integration facade tests | `src/openpi/src/openpi/integration/runtime_test.py`, `src/openpi/src/openpi/integration/artifacts_test.py`, `src/openpi/src/openpi/integration/training_test.py` |
| OpenPI script adapter tests | `src/openpi/scripts/train_adapter_test.py`, `src/openpi/scripts/serve_policy_test.py` |
| Mint OpenPI route, schema and artifact tests | `src/mint/tests/test_openpi_app_registration.py`, `src/mint/tests/test_openpi_config_validation.py`, `src/mint/tests/test_openpi_service_contract.py`, `src/mint/tests/test_openpi_does_not_pollute_tinker_types.py`, `src/mint/tests/test_openpi_artifact_proxy.py` |
| Mint to OpenPI runtime bridge tests | `src/mint/tests/test_openpi_runtime_bridge.py` |
| Mint OpenPI async training contract tests | `src/mint/tests/test_openpi_training_contract.py` |
| Toolkit `mint.openpi.*` namespace tests | `src/mindlab-toolkit/tests/test_openpi_namespace_contract.py` |
| Toolkit OpenPI SDK contract tests | `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py` |
| Toolkit to Mint live service smoke | `src/mint/tests/test_openpi_live_service_smoke.py` |
| Toolkit to deployed Mint remote smoke | `src/mint/tests/test_openpi_remote_deployment_smoke.py` |
| deterministic cross-repo closed loop | `src/mint/tests/test_openpi_cross_repo_closed_loop.py` |
| cross-repo live-service smoke | `src/mint/tests/test_openpi_live_service_smoke.py` |
| cross-repo remote deployment smoke | `src/mint/tests/test_openpi_remote_deployment_smoke.py` |
| release matrix by repo/version combination | documented in `docs/progress/openpi-compatibility-matrix.md` |
| service-hosted local checkpoint-layout round-trip | `src/mint/tests/test_openpi_live_service_smoke.py` |

## Positive And Negative Signals To Preserve

| Area | Positive signal | Negative signal |
| --- | --- | --- |
| OpenPI | deterministic runtime/artifact/training tests, script adapter tests and LoRA tests still pass after facade extraction | script adapters stop delegating or local training smoke breaks |
| Mint | OpenPI config gate, schema isolation, inference bridge, artifact proxy and training envelope pass without touching token-only types | old `/api/v1` path changes semantics, token-only types gain OpenPI fields, new OpenPI path returns ambiguous HTTP errors, or artifact route leaks non-checkpoint paths |
| Toolkit | `mint.openpi.*` imports and behaves as designed | top-level `mint.*` re-export or existing patch behavior changes |
| Cross-repo | deterministic fake-runtime loop works end-to-end | failure cannot be localized to runtime vs service vs SDK |

## Failure Attribution Rule

When a future cross-repo test fails, the write-up must classify it into one of these buckets first:

- `src/openpi` runtime surface failure
- `src/mint` service/schema/bridge failure
- `src/mindlab-toolkit` SDK/namespace failure
- environment or external asset failure

Do not write “OpenPI integration failed” without this classification.

## Current Environment-Specific Failures

- `src/openpi/src/openpi/models/model_test.py` 当前在本机 GPU 上失败于模型初始化阶段的 `RESOURCE_EXHAUSTED`。堆栈停在 `pi0` / `pi0_fast` model create，不经过 `openpi.integration.*`。
- 当前环境直接跑 `pytest` 会被外部 ROS 插件污染 collection；`src/openpi` 和 `src/mindlab-toolkit` 验证都需要显式设置 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`。
- `src/mindlab-toolkit` 的 `uv sync` 默认不会安装 `pytest`；干净环境下运行 Toolkit hard gate 需要显式使用 `uv run --with pytest ...`。
- 并发运行 `train_test.py` 与其他 JAX tests 会污染设备初始化状态，可能把原本可通过的 `lora_test.py` 拖成 CUDA backend init failure。当前 `src/openpi` 验证应串行执行。
- `src/mindlab-toolkit` 当前 `uv run` 默认拉起 CPython 3.14.2，`tinker` 会发出 “Pydantic V1 functionality isn't compatible with Python 3.14 or greater” warning。当前 Toolkit tests 可通过，但这不是 Python 3.14 clean-support 证明。

## Current Release Discipline

- 当前 release identity tuple 见 `docs/progress/openpi-compatibility-matrix.md`。
- 改 OpenPI contract 时，先更新 progress docs，再更新 owning repo tests，再更新代码。
- 当前 `src/openpi`、`src/mindlab-toolkit` 和 `src/mint` 都已有 repo-native workflow；本文件保留本地命令作为复现实验和故障归因入口。

## First Deterministic Closed-Loop Rule

The first cross-repo closed loop must satisfy all of these constraints:

- no external checkpoint download
- no `manual` marker
- no websocket server dependency
- fake runtime or test double allowed
- verifies structured observation/action payload
- verifies at least one lifecycle signal such as `reset()` or action chunk boundary
