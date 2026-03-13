# ST-09 Mint-Native OpenPI SFT Contract

## Current Status

- Status: in_progress

## Objective

把当前只接受 `config_name` / `exp_name` 的 OpenPI training bridge 扩成隔离的 Mint-native SFT 参数接口，使 Mint 用户可以在保留 OpenPI config family 作为 template anchor 的前提下，显式覆盖常用训练超参，而不是只能把 registry entry 当成完全黑盒。

## Why This Exists

当前 `/api/v1/openpi/training/start` 的真实语义仍然是：

- 选择一个 `src/openpi/src/openpi/training/config.py` 里的 config entry
- 用少量 envelope 字段覆盖 `exp_name` / `backend` / `overwrite` / `resume`
- 调用 `openpi.run_training(...)`

这条 bridge 足以证明 OpenPI training facade 可被 Mint 调起，但它不是 Mint-native SFT contract，因为：

- 常用训练超参仍藏在 OpenPI config registry 里
- Mint SDK 侧没有显式的 SFT 请求类型
- 后续 RL 线也无法在这种“裸 config bridge”上继续扩展而不污染其他模型族

## Repositories In Scope

- `src/mint`
- `src/openpi`
- `src/mindlab-toolkit`

## Current Topology Signals

- `src/mint/tinker_server/openpi/models.py` 当前同时承载 low-level `OpenPITrainingStartRequest` 和 isolated SFT lane 的 `OpenPISFTTrainingStartRequest` / `OpenPISFTConfigOverrides`。
- `src/mint/tinker_server/openpi/backend.py` 当前保留 generic training bridge，并新增基于 `config_overrides` 白名单的 SFT bridge；两条 lane 都通过 `openpi.training.config.get_config()` 加载 registry entry，再在 Mint 侧组装少量显式覆盖。
- `src/mindlab-toolkit/src/mint/openpi/client.py` 当前同时提供 `start_training()` 和 `start_sft_training()`；SFT 请求 payload 已经从五字段 generic bridge 扩成 `config_name` anchor 加 `config_overrides` 白名单。
- `src/openpi/src/openpi/training/config.py` 已经有可复用的 training dataclass surface，包括 `TrainConfig`、`DataConfigFactory`、`AssetsConfig`、`DataConfig`、optimizer / lr schedule dataclass。
- `src/mint/tinker_server/routes/training.py` 证明 Mint 主系统已经存在明确的 SFT / RL 语义分叉，但这些语义不能直接复用到 OpenPI plane，否则会污染其他模型族。

## Planned Direction

- 保留现有 `/api/v1/openpi/training/start` 作为 low-level bridge，不改写其既有 contract。
- 在 OpenPI route family 下新增 isolated SFT route，而不是复用 Mint 通用 training routes。
- SFT request 继续以 `config_name` 作为 OpenPI template anchor，但新增 `config_overrides` 白名单。
- v1 `config_overrides` 只覆盖 OpenPI `TrainConfig` 上已经稳定存在、且不要求序列化复杂内部对象的顶层字段：
  - `batch_size`
  - `num_train_steps`
  - `log_interval`
  - `save_interval`
  - `keep_period`
  - `wandb_enabled`
  - `seed`
- `checkpoint_base_dir`、`exp_name`、`overwrite`、`resume` 继续由 Mint bridge 持有，不下放给客户端。
- 顶层未知请求字段与未知 `config_overrides` 字段都必须 fail-fast 返回 422，不能静默忽略。
- 不在 v1 暴露 `model`、`data`、`weight_loader`、`optimizer`、`lr_schedule`、`freeze_filter` 这类会把 Mint 变成 OpenPI config authoring layer 的内部对象。
- result / future payload 继续走 OpenPI route family 和 Mint generic future contract，但要能把 SFT lane 与 low-level generic training lane 区分开。
- `mint://openpi/sft/<config>/<exp>/<step>` 是 Mint 对外暴露的 SFT alias，不要求底层持久化目录额外插入 `sft/`；artifact/archive/resume round-trip 仍必须回到 OpenPI 真实 checkpoint tree。
- Toolkit 需要提供独立 `mint.openpi` SFT client method，而不是让用户继续手写原始 JSON。

## Expected Outcomes

- Mint 用户可以在 OpenPI namespace 下显式提交 SFT 任务，并覆盖常用训练超参，而不再只能接受 registry entry 的默认值。
- `src/openpi` 仍然保有训练 runtime truth；Mint 只负责 contract、override 组装和服务封装。
- 现有 Mint 其他模型族与 Tinker-compatible training 路径不被影响。

## Non-Goals

- 一次性暴露 OpenPI `TrainConfig` 的全部字段
- 把 RL 训练面和 SFT 训练面混在同一批 contract 里
- 在这条子目标里解决 remote deployment owner、base URL、real checkpoint fixture
- 修改 `src/tinker`

## Dependencies

### Upstream

- `ST-03 Mint OpenPI Service Plane`
- `ST-04 Mindlab Toolkit OpenPI SDK`
- `ST-05 Cross-Repo Validation And Compatibility`
- `ST-07 Capability Negotiation And Skew Detection`

### Downstream

- `ST-10 Mint-Native OpenPI RL Contract`

## Guidance For Later Work

- 如果某个 override 无法映射到 `src/openpi` 已存在的 dataclass 顶层字段，就不要在 Mint contract 里伪造它。
- 如果某个 override 会要求通过 HTTP 传输 `model`、`data`、`optimizer` 或 server-local path，它不属于这个 v1 contract。
- 如果 future payload 仍然只返回 generic `openpi_training_result`，SDK 至少要能从 route / method 侧维持语义分离；更理想的是显式区分 payload type。
- 如果后续要扩成更深的 dataset / weight-loader authoring surface，应优先扩 `src/openpi` 的 dataclass/runtime facade，再扩 Mint contract。
