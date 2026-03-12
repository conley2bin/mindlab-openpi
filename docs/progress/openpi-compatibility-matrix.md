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
| Mint OpenPI service plane | `src/mint` | inference + artifact + training endpoints exist | gated OpenPI route family with inference, read-only artifact proxy and async training start | `src/mint/tests/test_openpi_app_registration.py`, `src/mint/tests/test_openpi_config_validation.py`, `src/mint/tests/test_openpi_service_contract.py`, `src/mint/tests/test_openpi_does_not_pollute_tinker_types.py`, `src/mint/tests/test_openpi_runtime_bridge.py`, `src/mint/tests/test_openpi_artifact_proxy.py`, `src/mint/tests/test_openpi_training_contract.py`, `src/mint/tests/test_issue_190_checkpoint_archive_auth_signed_url.py`, `src/mint/tests/test_issue_218_gateway_checkpoint_proxy.py`, `src/mint/tests/test_issue_281_scheduler_and_healthz.py` | none | current Mint Tinker-compatible anchors above | OpenPI disabled 仍是默认行为；training start 走 FutureStore-backed async envelope；`src/mint/tinker_server/models/types.py` 仍保持 token-only；当前 `/api/v1/openpi/status`、`/api/v1/openpi/infer`、`/api/v1/openpi/artifacts/resolve`、`/api/v1/openpi/artifacts/archive`、`/api/v1/openpi/training/start` 和 `/internal/openpi/status` 都会返回 `X-Mint-OpenPI-Negotiated-Capability`。 |
| Toolkit Tinker-compatible namespace | `src/mindlab-toolkit` | exists | patched tinker export surface under `mint.*` and `mint.tinker.*` | `src/mindlab-toolkit/tests/test_namespace_contract.py`, `src/mindlab-toolkit/tests/test_mint_polling_patch.py` | none | same must-pass list | 旧兼容层保持原义；新增 OpenPI namespace 后这些 anchors 仍是最硬的负向回归面。 |
| Toolkit OpenPI namespace | `src/mindlab-toolkit` | namespace + client + explicit transport exist | `mint.openpi.*` client surface for status, infer, artifacts, training start and future query | `src/mindlab-toolkit/tests/test_openpi_namespace_contract.py`, `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`, `src/mindlab-toolkit/tests/test_namespace_contract.py`, `src/mindlab-toolkit/tests/test_mint_polling_patch.py` | none | existing namespace and patch anchors above | `pyproject.toml` 现在显式依赖 `httpx`；默认 `User-Agent` 为 `MintOpenPI/Python ...`，不会触发 Mint 现有 Tinker client heuristic；SDK 会对未知 `openpi_*` future payload type fail-fast，支持 `Content-Disposition: filename*=` 文件名解析，吸收 Mint 当前 `status/capabilities` status payload，并在 negotiated capability header 存在且 mismatch 时抛 `OpenPIClientError`；header 缺失仍按旧服务兼容处理。 |
| Cross-repo deterministic closed loop | shared | fake-runtime status + inference + artifact + training/future loop exists | Mint status probe plus fake runtime/service-hosted artifact and async training path to Toolkit SDK | `src/mint/tests/test_openpi_cross_repo_closed_loop.py` | none | Mint and Toolkit existing anchors | harness 当前落在 `src/mint/tests/`；使用 fake runtime / fake future store / local checkpoint dir，不依赖外网和真实 checkpoint，并验证了 status contract、structured payload、artifact transport、training future pending/failure/success envelope 与 `reset()` lifecycle。 |
| Cross-repo localhost live-service smoke | shared | status + inference + artifact resolve/archive + training/future over real HTTP exists | Toolkit SDK to Mint OpenPI service over localhost TCP transport | `src/mint/tests/test_openpi_live_service_smoke.py` | none | Mint and Toolkit existing anchors | 这条 lane 使用 uvicorn 起本地服务，保留 fake runtime / fake future store 与本地 checkpoint 目录，只验证真实 HTTP transport、route registration、artifact resolve/archive 和 background task 路径。 |
| Cross-repo remote deployment smoke | shared | opt-in env-driven status + artifact + optional real-checkpoint infer smoke exists | Toolkit SDK to deployed Mint OpenPI service outside localhost | `src/mint/tests/test_openpi_remote_deployment_smoke.py` | none | Mint and Toolkit existing anchors | 这条 lane 默认不运行；需要显式设置 `MINT_OPENPI_REMOTE_SMOKE=1` 和远端绝对 URL 形式的 base URL。artifact/archive 需要 checkpoint env；real-checkpoint infer 还需要 config/observation env。失败会按 `environment` / `deployment` / `runtime` / `service` / `sdk` 分桶；base URL 缺失 / 非绝对 URL、malformed / non-finite timeout，以及 malformed / non-object observation JSON 都会显式归到 `environment`，但它还不是 hard gate。 |
| Cross-repo real-asset lane | shared | service-hosted local checkpoint-layout round-trip exists; real checkpoint/manual inference remains exploratory | Mint artifact resolve/archive over actual checkpoint tree, plus separate real checkpoint inference validation | `src/mint/tests/test_openpi_live_service_smoke.py` | `src/openpi/src/openpi/policies/policy_test.py`, `src/openpi/src/openpi/shared/download_test.py` | Mint and Toolkit existing anchors | `src/mint/tests/test_openpi_live_service_smoke.py` 现在会触发 Mint 的 checkpoint URI 解析、persistent-cache materialization 和 tar.gz archive stream，并校验真实本地 checkpoint layout 的文件内容；remote download 和实际模型推理仍留在 exploratory lane。 |

## First-Cut Coverage Decision

| Capability cut | Current repo evidence | Use in first implementation cut | Status |
| --- | --- | --- | --- |
| deterministic status + inference + artifact + training/future closed loop | `src/openpi/src/openpi/integration/runtime_test.py`, `src/mint/tests/test_openpi_service_contract.py`, `src/mint/tests/test_openpi_runtime_bridge.py`, `src/mint/tests/test_openpi_artifact_proxy.py`, `src/mint/tests/test_openpi_training_contract.py`, `src/mint/tests/test_openpi_cross_repo_closed_loop.py`, `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py` | yes | completed |
| localhost real-HTTP status + inference + artifact resolve/archive + training/future smoke | `src/mint/tests/test_openpi_live_service_smoke.py` | yes | completed |
| service-hosted local checkpoint-layout artifact round-trip | `src/mint/tests/test_openpi_live_service_smoke.py` | yes | completed |
| remote deployment status + artifact + optional real-checkpoint infer smoke | `src/mint/tests/test_openpi_remote_deployment_smoke.py` | no, opt-in only | in_progress |
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

## Current Release Discipline

### Current identity tuple

| Layer | Current identity | Evidence |
| --- | --- | --- |
| Mint service package | `tinker-server==0.1.0` | `src/mint/pyproject.toml` |
| Toolkit distribution | `mindlab-toolkit==0.0.1` | `src/mindlab-toolkit/pyproject.toml` |
| Toolkit Mint compatibility version | `MINT_VERSION=0.1.0` and `tinker==0.6.0` | `src/mindlab-toolkit/src/mint/mint/__init__.py`, `src/mindlab-toolkit/pyproject.toml` |
| Toolkit OpenPI transport identity | `MintOpenPI/Python 0.1.0` plus `OPENPI_CAPABILITY_VERSION=0.1` | `src/mindlab-toolkit/src/mint/openpi/config.py` |
| OpenPI runtime package | `openpi==0.1.0` | `src/openpi/pyproject.toml` |
| OpenPI client package | `openpi-client==0.1.0` | `src/openpi/packages/openpi-client/pyproject.toml` |

### Current capability contract

| Concern | Current truth | Owner | Evidence |
| --- | --- | --- | --- |
| request-side transport identity | Toolkit 发送 `X-Mint-OpenPI-Capability: 0.1` | `src/mindlab-toolkit` | `src/mindlab-toolkit/src/mint/openpi/config.py`, `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py` |
| response-side negotiated signal | Mint OpenPI route family 返回 `X-Mint-OpenPI-Negotiated-Capability: 0.1` | `src/mint` | `src/mint/tinker_server/openpi/routes.py`, `src/mint/tests/test_openpi_runtime_bridge.py` |
| client-side skew detection | Toolkit 在 negotiated header 存在且 mismatch 时抛 `OpenPIClientError`；header 缺失保持兼容 | `src/mindlab-toolkit` | `src/mindlab-toolkit/src/mint/openpi/client.py`, `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py` |

Generic `retrieve_future` 仍属于 Mint 通用 future contract，当前不要求它返回 OpenPI-negotiated header；SDK 因此只在 header 存在时校验。

### Required update order for contract changes

1. Update `docs/progress/openpi-compatibility-matrix.md` and `docs/progress/openpi-validation-baseline.md` first.
2. Update the owning repo contract tests next.
3. Update runtime/service/SDK code only after the new gate is written down.
4. Re-run repo-local gates plus `src/mint/tests/test_openpi_cross_repo_closed_loop.py` and `src/mint/tests/test_openpi_live_service_smoke.py`.
5. Only then cut or merge a release combination; do not assume the three repos move in lockstep.

### Workflow reality today

- `src/openpi/.github/workflows/test.yml` exists and runs repo-local deterministic tests.
- `src/mindlab-toolkit/.github/workflows/test.yml` now exists and runs the documented OpenPI/Tinker namespace gates via `uv run --with pytest`.
- `src/mint/.github/workflows/test.yml` now exists and runs the documented OpenPI/Tinker service gates via `uv sync --frozen --extra dev` plus `uv run pytest`.
- Local commands in `docs/progress/openpi-validation-baseline.md` remain the canonical reproduction steps when workflow failures need local diagnosis.

## Missing Entries That Must Appear Later

- deployment-owned remote smoke target plus credential provisioning policy
- service-hosted real-checkpoint validation with a stable observation fixture and checkpoint fixture
- structured capability matrix beyond the current single negotiated version string
