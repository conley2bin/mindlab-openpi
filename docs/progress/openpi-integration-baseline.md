# OpenPI Integration Baseline

Baseline date: 2026-03-12

## Scope

这份文档只记录当前代码现实、当前缺口和当前主线起点。它不定义长期目标，也不替代实施方案。

## Repo Reality

| Repo | Current truth | Hard anchors | Missing for integration |
| --- | --- | --- | --- |
| `src/openpi` | 已有 standalone inference、policy 装配、training scripts、checkpoint 逻辑和 `openpi-client`。当前 canonical inference/artifact/training 装配已经开始收敛进 `src/openpi/src/openpi/integration/{runtime,artifacts,training}.py`。`src/openpi/src/openpi/policies/policy_config.py`、`src/openpi/scripts/serve_policy.py` 和 `src/openpi/scripts/train_test.py` 已经转向 integration-facing surface；`src/openpi/scripts/train.py`、`src/openpi/scripts/train_pytorch.py` 仍保留 backend implementation。 | `src/openpi/src/openpi/policies/policy.py`, `src/openpi/src/openpi/integration/runtime.py`, `src/openpi/src/openpi/integration/artifacts.py`, `src/openpi/src/openpi/integration/training.py`, `src/openpi/src/openpi/training/checkpoints.py`, `src/openpi/scripts/serve_policy_test.py`, `src/openpi/scripts/train_test.py` | 训练脚本还没有完全退回 CLI adapter。顶层 stable export 也还没有只暴露 integration surface。 |
| `src/mint` | 当前 public service surface 是 Tinker-compatible token/chunk API。`src/mint/tinker_server/app.py` 只注册 `/api/v1` 下的 `service`、`sampling`、`futures`、`training`、`weights`，以及 `/internal`。`src/mint/tinker_server/models/types.py` 明确服务于 tinker client compatibility。 | `src/mint/tinker_server/app.py`, `src/mint/tinker_server/models/types.py`, `src/mint/tests/test_gateway_multi_target_routing.py`, `src/mint/tests/test_client_compat_user_agent.py`, `src/mint/tests/test_tinker_prompt_logprobs_semantics.py` | 不存在 `src/mint/tinker_server/openpi/` package，不存在 OpenPI-specific route family、schema family、runtime bridge、config section。 |
| `src/mindlab-toolkit` | 当前 package 的主体是 “patched tinker compatibility layer”。`src/mindlab-toolkit/src/mint/__init__.py` 导入时会先执行 `apply_mint_patches()`，然后把 `mint.tinker` 的导出 re-export 到顶层 `mint.*`。 | `src/mindlab-toolkit/src/mint/__init__.py`, `src/mindlab-toolkit/src/mint/tinker/__init__.py`, `src/mindlab-toolkit/src/mint/mint/__init__.py`, `src/mindlab-toolkit/tests/test_namespace_contract.py`, `src/mindlab-toolkit/tests/test_mint_polling_patch.py` | 不存在 `src/mindlab-toolkit/src/mint/openpi/` namespace。`pyproject.toml` 当前只有 `tinker==0.6.0` 依赖，没有 OpenPI service client transport 依赖。 |

## Cross-Repo Reality

- 目前没有任何一条从 `src/openpi` runtime 到 `src/mint` service 再到 `src/mindlab-toolkit` SDK 的真实闭环。
- 目前没有 compatibility matrix。
- 目前没有 deterministic cross-repo closed loop。
- 目前没有任何 OpenPI-specific repo-local contract test，因为三个 owning surfaces 都还不存在。

## Semantic Split Observed Today

- `src/mint` 当前核心语义是 token/chunk、sampling session、training model、future retrieval。
- `src/openpi` 当前核心语义是 observation/action/multimodal payload、policy `infer(obs)`、`reset()`、action chunk。
- `src/mindlab-toolkit` 当前核心语义不是 OpenPI client，而是 Tinker-compatible SDK 的 Mint re-export 和 patch layer。

这三套语义今天还没有被一个中间层收敛起来。

## Immediate Gaps By Subtarget

| ST | Current gap |
| --- | --- |
| `ST-01` | 当前没有 baseline 文档和 glossary。三仓术语还没有被写成单一 reference。 |
| `ST-02` | inference、artifact、training facade 已落地，但 training/serving 脚本还未完全退回 adapter，stable export 也还没收口。 |
| `ST-03` | `src/mint` 没有 OpenPI service plane。现有 public schema 全是 token-centric。 |
| `ST-04` | `src/mindlab-toolkit` 没有 `mint.openpi.*` namespace，也没有 transport dependency 决策。 |
| `ST-05` | 没有 compatibility matrix，没有 deterministic closed loop，没有统一 gate policy。 |

## Current Working Cut For The First Implementation Pass

这不是“已经支持”的范围，而是当前文档链收敛后的首批切面。

- 首批闭环只做 inference-only。
- 首批 deterministic local lane 不依赖真实 checkpoint，使用 fake runtime 或 test double。
- 首批 real-asset exploratory lane 以 `pi0_aloha_sim` 为代表，因为：
  - `src/openpi/src/openpi/policies/policy_test.py` 当前使用 `pi0_aloha_sim`
  - `src/openpi/scripts/serve_policy.py` 当前对 ALOHA simulator 的默认 checkpoint 也是 `pi0_aloha_sim`
- 首批 local training smoke 继续以 `src/openpi/scripts/train_test.py` 的 `debug` config 为锚点，并且该锚点现在通过 `openpi.integration.training` 进入训练 contract。
- `pi05_*` 和 `pi0_fast_*` 当前不进入第一条 Mint closed loop；它们保留在后续兼容矩阵扩展里。

## Risks Already Visible

- 如果先做 Mint route，再做 `src/openpi` facade，Mint 会被迫直接依赖研究期内部对象。
- 如果先做 Toolkit SDK，再做 Mint service contract，SDK 会被迫猜 service schema。
- 如果不把旧路径回归测试固定成门禁，OpenPI 接入很容易通过修改旧断言来“放行”路径污染。
- `scripts/train.py` 的 JAX resume 路径当前依赖 “resumed state 不做 donation” 这个实现约束；后续如果再次改动 `jax.jit(... donate_argnums=...)`，必须重新验证 `scripts/train_test.py`。
