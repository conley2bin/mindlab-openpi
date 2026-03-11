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
  tests/test_issue_281_scheduler_and_healthz.py \
  tests/test_tinker_prompt_logprobs_semantics.py \
  tests/test_openpi_app_registration.py \
  tests/test_openpi_config_validation.py \
  tests/test_openpi_service_contract.py \
  tests/test_openpi_does_not_pollute_tinker_types.py \
  tests/test_openpi_runtime_bridge.py -q
```

What these gates cover:

- config file validation
- model registry env overrides
- gateway multi-target routing behavior
- client user-agent compatibility logic
- healthz and route labeling behavior
- prompt logprobs semantics for the Tinker-compatible path
- OpenPI config gate and app registration behavior
- OpenPI schema isolation from token-only types
- OpenPI inference runtime bridge and HTTP status mapping

What these gates do not cover:

- OpenPI artifact proxy
- OpenPI training endpoints
- toolkit namespace / SDK contract

### `src/mindlab-toolkit`

```bash
cd src/mindlab-toolkit && pytest \
  tests/test_namespace_contract.py \
  tests/test_mint_polling_patch.py -q
```

What these gates cover:

- current top-level namespace contract
- current patch side effects for the Tinker-compatible layer

What these gates do not cover:

- `mint.openpi.*`
- OpenPI service client transport
- SDK mapping to Mint OpenPI service schemas

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
| Mint OpenPI route and schema tests | `src/mint/tests/test_openpi_app_registration.py`, `src/mint/tests/test_openpi_config_validation.py`, `src/mint/tests/test_openpi_service_contract.py`, `src/mint/tests/test_openpi_does_not_pollute_tinker_types.py` |
| Mint to OpenPI runtime bridge tests | `src/mint/tests/test_openpi_runtime_bridge.py` |
| Toolkit `mint.openpi.*` namespace tests | missing |
| Toolkit OpenPI SDK contract tests | missing |
| deterministic cross-repo closed loop | missing |
| release matrix by repo/version combination | missing |

## Positive And Negative Signals To Preserve

| Area | Positive signal | Negative signal |
| --- | --- | --- |
| OpenPI | deterministic runtime/artifact/training tests, script adapter tests and LoRA tests still pass after facade extraction | script adapters stop delegating or local training smoke breaks |
| Mint | OpenPI config gate, schema isolation and inference bridge pass without touching token-only types | old `/api/v1` path changes semantics, token-only types gain OpenPI fields, or new OpenPI path returns ambiguous HTTP errors |
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
- 当前环境直接跑 `pytest` 会被外部 ROS 插件污染 collection；`src/openpi` 验证需要显式设置 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`。
- 并发运行 `train_test.py` 与其他 JAX tests 会污染设备初始化状态，可能把原本可通过的 `lora_test.py` 拖成 CUDA backend init failure。当前 `src/openpi` 验证应串行执行。

## First Deterministic Closed-Loop Rule

The first cross-repo closed loop must satisfy all of these constraints:

- no external checkpoint download
- no `manual` marker
- no websocket server dependency
- fake runtime or test double allowed
- verifies structured observation/action payload
- verifies at least one lifecycle signal such as `reset()` or action chunk boundary
