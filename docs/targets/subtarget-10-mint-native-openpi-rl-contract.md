# ST-10 Mint-Native OpenPI RL Contract

## Current Status

- Status: research

## Objective

为未来 Mint-native OpenPI RL 训练面先固定边界、依赖和缺口，避免在 `src/openpi` 还没有真实 RL runtime 时，Mint 侧先长出一个无 owner 的伪接口。

## Why This Exists

用户侧已经明确要求把 OpenPI 训练能力拆成 SFT 和 RL 两条语义线，但当前代码现实是：

- `src/openpi` 现在有 inference、artifact 和 supervised training facade
- `src/openpi` 当前没有等价于 Mint `ppo` / `importance_sampling` / rollout correction 的独立 RL runtime surface
- `src/mint` 通用 training 路径已有 RL loss 语义，但这些语义属于现有 LLM / Megatron / verl 训练栈，不等于 OpenPI 训练 runtime

因此，当前最合理的做法不是直接实现一个 RL API，而是先把边界固定下来：

- RL contract 必须落在 OpenPI namespace 内
- 它不能复用 Mint 现有通用 training route 来“假装支持”
- 它必须以 `src/openpi` 拥有真实 runtime / algorithm owner 为前提

## Repositories In Scope

- `src/mint`
- `src/openpi`
- `src/mindlab-toolkit`

## Current Topology Signals

- `src/mint/tinker_server/routes/training.py` 与 `src/mint/tinker_server/backend/megatron_distributed.py` 已经承载 `cross_entropy`、`ppo`、`importance_sampling` 与 rollout correction，这条线属于现有 Mint 训练栈。
- `src/mint/tinker_server/models/types.py` 的 `RolloutCorrectionConfig` 明确写着它镜像的是 `verl` 的 `policy_loss.rollout_correction` schema；这是 Mint/verl 语义，不是 OpenPI public contract。
- `src/openpi/src/openpi/integration/training.py` 当前只暴露 `run_training` / `run_jax_training` / `run_pytorch_training` 这条 supervised training dispatch，没有 rollout/reward/update 语义，也没有独立 RL trainer facade。
- `src/openpi/src/openpi/training/data_loader.py` 与 `src/openpi/src/openpi/training/config.py` 虽然有 `RLDS*` 数据加载配置，但它们处理的是 dataset / loader / checkpoint 语义，不等于 RL rollout / reward / policy-loss runtime。
- `src/openpi/src/openpi/training/data_loader.py` 里的 `create_rlds_data_loader()` 甚至还显式说明 PyTorch RLDS data loader 不支持；这再次说明当前存在的是数据输入形态，不是完整 RL runtime owner。

## Planned Direction

- 先完成 `ST-09`，把 OpenPI training interface 从 “裸 config bridge” 提升到 isolated SFT contract。
- 在 `src/openpi` 真正出现 RL runtime owner 前，`ST-10` 只做 contract research，不新增对外 API。
- 后续如果要启动 RL 接口，第一步必须先在 `src/openpi` 确认：
  - RL runtime owner
  - reward / rollout / dataset semantics
  - checkpoint / policy / actor update contract
  - 与现有 Mint RL 训练栈的复用边界
- 如果上述 owner surface 真的落地，再进入 Mint / Toolkit：
  - Mint 才能新增 isolated `/api/v1/openpi/training/rl/start`
  - Toolkit 才能新增 `mint.openpi` RL client types
  - cross-repo fake-runtime lane 和 localhost live-service smoke 才能扩到 RL

## Expected Outcomes

- 后续 RL 工作不会误把 Mint 现有通用 training route 当成 OpenPI 的临时替代品。
- `src/openpi`、`src/mint`、`src/mindlab-toolkit` 对 RL 接口 owner 的认知保持一致。

## Non-Goals

- 在当前阶段承诺完整 RL 训练算法或运行时
- 在 Mint 侧先实现一个没有 OpenPI runtime owner 的 RL API
- 让现有 Mint 其他模型族为 OpenPI RL 需求背负兼容负担

## Dependencies

### Upstream

- `ST-09 Mint-Native OpenPI SFT Contract`

### Downstream

- 无

## Guidance For Later Work

- 如果 `src/openpi` 还没有 RL runtime facade，就不要在 `src/mint` 或 `src/mindlab-toolkit` 侧创造表面兼容层。
- 如果代码里只出现 `RLDS*` dataset / loader config，这仍然不构成 RL runtime owner。
- 如果未来 RL contract 需要复用 Mint 现有 `ppo` / `importance_sampling` 术语，必须明确哪些字段是 OpenPI 语义，哪些字段只是现有 Mint trainer 的实现细节。
- 如果后续真的新增 `/api/v1/openpi/training/rl/start`，它必须和 generic training、SFT 一样保持 route/type/result 隔离，不能回退到通用 training route 膨胀。
