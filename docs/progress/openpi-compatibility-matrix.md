# OpenPI Compatibility Matrix

Matrix date: 2026-03-12

## Scope

这份 matrix 记录当前支持面、owner repo、验证锚点和未开始项。它不是未来路线图。

## Surface Matrix

| Layer | Owner repo | Current status | Representative capability | Must-pass local anchors | Exploratory anchors | Negative regression anchors | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenPI runtime internals | `src/openpi` | exists | model create, policy infer, training loop, checkpoint handling | `src/openpi/src/openpi/models/model_test.py`, `src/openpi/src/openpi/models/lora_test.py`, `src/openpi/scripts/train_test.py` | `src/openpi/src/openpi/policies/policy_test.py`, `src/openpi/src/openpi/shared/download_test.py` | `src/openpi/scripts/train_test.py` also guards script compatibility | `model_test.py` 当前仍在本机 GPU 上 OOM；`train_test.py` 现在是可通过的 debug start/resume smoke，不应再把它归类成环境 abort。 |
| OpenPI integration facade | `src/openpi` | inference + artifact + training exists | library-level inference/artifact/training facade for Mint | `src/openpi/src/openpi/integration/runtime_test.py`, `src/openpi/src/openpi/integration/artifacts_test.py`, `src/openpi/src/openpi/integration/training_test.py`, `src/openpi/scripts/serve_policy_test.py`, `src/openpi/scripts/train_test.py` | none | `src/openpi/src/openpi/models/lora_test.py` | `training` facade 已吸收 JAX/PyTorch dispatch contract；`scripts/train_test.py` 已改成通过 `openpi.integration.training` 走 debug/resume 闭环。 |
| Mint Tinker-compatible service | `src/mint` | exists | token/chunk `/api/v1` routes, sampling session, training model, futures | `src/mint/tests/test_issue_136_config_file_validation.py`, `src/mint/tests/test_model_registry_env_config.py`, `src/mint/tests/test_gateway_multi_target_routing.py`, `src/mint/tests/test_client_compat_user_agent.py`, `src/mint/tests/test_tinker_prompt_logprobs_semantics.py` | 其他 issue regression tests under `src/mint/tests/` | same must-pass list | 这是当前最硬的负向回归面。 |
| Mint OpenPI service plane | `src/mint` | not started | OpenPI route family, schema family, runtime bridge, artifact proxy | none | none | current Mint Tinker-compatible anchors above | 不能污染 `src/mint/tinker_server/models/types.py`。 |
| Toolkit Tinker-compatible namespace | `src/mindlab-toolkit` | exists | patched tinker export surface under `mint.*` and `mint.tinker.*` | `src/mindlab-toolkit/tests/test_namespace_contract.py`, `src/mindlab-toolkit/tests/test_mint_polling_patch.py` | none | same must-pass list | 当前只有 compatibility layer，没有 OpenPI namespace。 |
| Toolkit OpenPI namespace | `src/mindlab-toolkit` | not started | `mint.openpi.*` client surface | none | none | existing namespace and patch anchors above | 当前也没有 transport dependency。 |
| Cross-repo deterministic closed loop | shared | not started | fake runtime to Mint service to Toolkit SDK | none | none | Mint and Toolkit existing anchors | 首条闭环必须不依赖外网和真实 checkpoint。 |
| Cross-repo real-asset lane | shared | not started | real checkpoint inference validation | none | `src/openpi/src/openpi/policies/policy_test.py`, `src/openpi/src/openpi/shared/download_test.py` | Mint and Toolkit existing anchors | 这是后置 lane，不是首批 gate。 |

## First-Cut Coverage Decision

| Capability cut | Current repo evidence | Use in first implementation cut | Status |
| --- | --- | --- | --- |
| deterministic inference-only closed loop | `src/openpi/src/openpi/integration/runtime_test.py`, `src/openpi/src/openpi/integration/artifacts_test.py` | yes | in progress |
| real-asset inference with `pi0_aloha_sim` semantics | `src/openpi/src/openpi/policies/policy_test.py`, `src/openpi/scripts/serve_policy.py` | yes, but exploratory only | selected |
| local training smoke with `debug` config | `src/openpi/scripts/train_test.py` | yes | selected |
| `pi05_*` inference/training | `src/openpi/scripts/serve_policy.py`, `src/openpi/src/openpi/training/config.py` | no | deferred |
| `pi0_fast_*` inference/training | `src/openpi/src/openpi/training/config.py`, `src/openpi/README.md` | no | deferred |

## Repo Owners

| Concern | Owner |
| --- | --- |
| OpenPI semantic objects and runtime errors | `src/openpi` |
| Mint service envelope, polling, auth, ops metadata | `src/mint` |
| Toolkit namespace, public imports, client ergonomics | `src/mindlab-toolkit` |
| Support table and gate policy | `docs/progress` |

## Missing Entries That Must Appear Later

- `src/mint/tests/test_openpi_app_registration.py`
- `src/mint/tests/test_openpi_service_contract.py`
- `src/mint/tests/test_openpi_runtime_bridge.py`
- `src/mint/tests/test_openpi_does_not_pollute_tinker_types.py`
- `src/mindlab-toolkit/tests/test_openpi_namespace_contract.py`
- `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`
