# OpenPI Compatibility Matrix

Matrix date: 2026-03-12

## Scope

这份 matrix 记录当前支持面、owner repo、验证锚点和未开始项。它不是未来路线图。

## Surface Matrix

| Layer | Owner repo | Current status | Representative capability | Must-pass local anchors | Exploratory anchors | Negative regression anchors | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenPI runtime internals | `src/openpi` | exists | model create, policy infer, training loop, checkpoint handling | `src/openpi/src/openpi/models/lora_test.py`, `src/openpi/src/openpi/training/config_test.py`, `src/openpi/scripts/train_test.py` | `src/openpi/src/openpi/models/model_test.py`, `src/openpi/src/openpi/policies/policy_test.py`, `src/openpi/src/openpi/shared/download_test.py` | `src/openpi/scripts/train_test.py`, `src/openpi/src/openpi/training/config_test.py` | `model_test.py` 当前仍在本机 GPU 上 OOM；`train_test.py` 是当前可通过的 debug start/resume smoke。 |
| OpenPI integration facade | `src/openpi` | inference + artifact + training exists | library-level inference/artifact/training facade for Mint | `src/openpi/src/openpi/integration/runtime_test.py`, `src/openpi/src/openpi/integration/artifacts_test.py`, `src/openpi/src/openpi/integration/training_test.py`, `src/openpi/scripts/serve_policy_test.py`, `src/openpi/scripts/train_test.py`, `src/openpi/scripts/train_adapter_test.py` | none | `src/openpi/src/openpi/models/lora_test.py` | `training` facade 已吸收 JAX/PyTorch dispatch contract；`scripts/train.py` 和 `scripts/train_pytorch.py` 已退回薄 adapter；`src/openpi/src/openpi/__init__.py` 现在只导出稳定 inference/training surface。 |
| Mint Tinker-compatible service | `src/mint` | exists | token/chunk `/api/v1` routes, sampling session, training model, futures | `src/mint/tests/test_issue_136_config_file_validation.py`, `src/mint/tests/test_model_registry_env_config.py`, `src/mint/tests/test_gateway_multi_target_routing.py`, `src/mint/tests/test_client_compat_user_agent.py`, `src/mint/tests/test_tinker_prompt_logprobs_semantics.py` | 其他 issue regression tests under `src/mint/tests/` | same must-pass list | 这是当前最硬的负向回归面。 |
| Mint OpenPI service plane | `src/mint` | inference + artifact + training endpoints exist | gated OpenPI route family with inference, read-only artifact proxy and async training start | `src/mint/tests/test_openpi_app_registration.py`, `src/mint/tests/test_openpi_config_validation.py`, `src/mint/tests/test_openpi_service_contract.py`, `src/mint/tests/test_openpi_does_not_pollute_tinker_types.py`, `src/mint/tests/test_openpi_runtime_bridge.py`, `src/mint/tests/test_openpi_artifact_proxy.py`, `src/mint/tests/test_openpi_training_contract.py`, `src/mint/tests/test_issue_190_checkpoint_archive_auth_signed_url.py`, `src/mint/tests/test_issue_218_gateway_checkpoint_proxy.py`, `src/mint/tests/test_issue_281_scheduler_and_healthz.py` | none | current Mint Tinker-compatible anchors above | OpenPI disabled 仍是默认行为；training start 走 FutureStore-backed async envelope；`src/mint/tinker_server/models/types.py` 仍保持 token-only。 |
| Toolkit Tinker-compatible namespace | `src/mindlab-toolkit` | exists | patched tinker export surface under `mint.*` and `mint.tinker.*` | `src/mindlab-toolkit/tests/test_namespace_contract.py`, `src/mindlab-toolkit/tests/test_mint_polling_patch.py` | none | same must-pass list | 旧兼容层保持原义；新增 OpenPI namespace 后这些 anchors 仍是最硬的负向回归面。 |
| Toolkit OpenPI namespace | `src/mindlab-toolkit` | namespace + client + explicit transport exist | `mint.openpi.*` client surface for status, infer, artifacts, training start and future query | `src/mindlab-toolkit/tests/test_openpi_namespace_contract.py`, `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`, `src/mindlab-toolkit/tests/test_namespace_contract.py`, `src/mindlab-toolkit/tests/test_mint_polling_patch.py` | none | existing namespace and patch anchors above | `pyproject.toml` 现在显式依赖 `httpx`；默认 `User-Agent` 为 `MintOpenPI/Python ...`，不会触发 Mint 现有 Tinker client heuristic；SDK 会对未知 `openpi_*` future payload type fail-fast，支持 `Content-Disposition: filename*=` 文件名解析，并吸收 Mint 当前 `status/capabilities` status payload。 |
| Cross-repo deterministic closed loop | shared | fake-runtime status + inference + artifact + training/future loop exists | Mint status probe plus fake runtime/service-hosted artifact and async training path to Toolkit SDK | `src/mint/tests/test_openpi_cross_repo_closed_loop.py` | none | Mint and Toolkit existing anchors | harness 当前落在 `src/mint/tests/`；使用 fake runtime / fake future store / local checkpoint dir，不依赖外网和真实 checkpoint，并验证了 status contract、structured payload、artifact transport、training future envelope 与 `reset()` lifecycle。 |
| Cross-repo real-asset lane | shared | not started | real checkpoint inference validation | none | `src/openpi/src/openpi/policies/policy_test.py`, `src/openpi/src/openpi/shared/download_test.py` | Mint and Toolkit existing anchors | 这是后置 lane，不是首批 gate。 |

## First-Cut Coverage Decision

| Capability cut | Current repo evidence | Use in first implementation cut | Status |
| --- | --- | --- | --- |
| deterministic status + inference + artifact + training/future closed loop | `src/openpi/src/openpi/integration/runtime_test.py`, `src/mint/tests/test_openpi_service_contract.py`, `src/mint/tests/test_openpi_runtime_bridge.py`, `src/mint/tests/test_openpi_artifact_proxy.py`, `src/mint/tests/test_openpi_training_contract.py`, `src/mint/tests/test_openpi_cross_repo_closed_loop.py`, `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py` | yes | completed |
| real-asset inference with `pi0_aloha_sim` semantics | `src/openpi/src/openpi/policies/policy_test.py`, `src/openpi/scripts/serve_policy.py` | yes, but exploratory only | selected |
| local training smoke with `debug` config | `src/openpi/scripts/train_test.py`, `src/openpi/scripts/train_adapter_test.py` | yes | selected |
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

- cross-repo live-service smoke lane
