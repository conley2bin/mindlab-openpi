# OpenPI Validation Baseline

Baseline date: 2026-03-12

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
  tests/test_model_registry_env_config.py \
  tests/test_gateway_multi_target_routing.py \
  tests/test_client_compat_user_agent.py \
  tests/test_issue_190_checkpoint_archive_auth_signed_url.py \
  tests/test_issue_218_gateway_checkpoint_proxy.py \
  tests/test_issue_281_scheduler_and_healthz.py \
  tests/test_tinker_prompt_logprobs_semantics.py \
  tests/test_openpi_app_registration.py \
  tests/test_openpi_config_validation.py \
  tests/test_openpi_service_contract.py \
  tests/test_openpi_does_not_pollute_tinker_types.py \
  tests/test_openpi_runtime_bridge.py \
  tests/test_openpi_artifact_proxy.py \
  tests/test_openpi_training_contract.py -q
```

What these gates cover:

- config file validation
- model registry env overrides
- gateway multi-target routing behavior
- client user-agent compatibility logic
- checkpoint archive auth and checkpoint proxy regressions around existing paths
- healthz and route labeling behavior
- prompt logprobs semantics for the Tinker-compatible path
- OpenPI config gate and app registration behavior
- OpenPI schema isolation from token-only types
- OpenPI inference runtime bridge and HTTP status mapping
- OpenPI artifact resolve/archive contract and checkpoint reference restrictions
- OpenPI training start async envelope, FutureStore queueing semantics and Mint-owned run/checkpoint URI mapping

What these gates do not cover:

- live Ray-backed FutureStore behavior under a real OpenPI training workload
- toolkit namespace / SDK contract
- deterministic cross-repo closed loop

### `src/mindlab-toolkit`

```bash
cd src/mindlab-toolkit && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run python -m pytest \
  tests/test_namespace_contract.py \
  tests/test_mint_polling_patch.py \
  tests/test_openpi_namespace_contract.py \
  tests/test_openpi_sdk_contract.py -q
```

What these gates cover:

- current top-level namespace contract
- current patch side effects for the Tinker-compatible layer
- explicit `mint.openpi.*` namespace contract
- OpenPI SDK config, distinct client identity, Mint OpenPI request envelopes, current Mint status payload decoding and future payload mapping

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
- Toolkit SDK to Mint OpenPI training start and generic `retrieve_future` closed loop
- structured observation/action payload across repo boundaries
- Mint-owned artifact resolve summary and archive transport contract
- Mint-owned async training future envelope and typed training result decode
- lifecycle signal propagation via `reset_before_infer`

What this gate does not cover:

- real checkpoint model loading
- live deployment networking
- real-asset artifact end-to-end round-trips

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
| Toolkit to Mint live service smoke | missing |
| deterministic cross-repo closed loop | `src/mint/tests/test_openpi_cross_repo_closed_loop.py` |
| cross-repo live-service smoke | missing |
| release matrix by repo/version combination | missing |

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
- 并发运行 `train_test.py` 与其他 JAX tests 会污染设备初始化状态，可能把原本可通过的 `lora_test.py` 拖成 CUDA backend init failure。当前 `src/openpi` 验证应串行执行。
- `src/mindlab-toolkit` 当前 `uv run` 默认拉起 CPython 3.14.2，`tinker` 会发出 “Pydantic V1 functionality isn't compatible with Python 3.14 or greater” warning。当前 Toolkit tests 可通过，但这不是 Python 3.14 clean-support 证明。

## First Deterministic Closed-Loop Rule

The first cross-repo closed loop must satisfy all of these constraints:

- no external checkpoint download
- no `manual` marker
- no websocket server dependency
- fake runtime or test double allowed
- verifies structured observation/action payload
- verifies at least one lifecycle signal such as `reset()` or action chunk boundary
