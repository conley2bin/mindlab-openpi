# OpenPI Training Surfaces Design

日期：2026-03-13

## Context

当前 OpenPI service plane 已有 inference、artifact 和 generic training bridge。generic training bridge 只接受 `config_name`、`exp_name`、`backend`、`overwrite`、`resume`。这说明 Mint 可以调起 OpenPI training facade，但还没有形成 Mint-native 训练参数面。

同时存在三条不同工作线：

- remote deployment / URL smoke：验证远端部署、base URL、real checkpoint、real observation fixture
- Mint-native SFT：把 supervised fine-tuning 参数从 registry-name bridge 展开成显式 contract
- Mint-native RL：等待 `src/openpi` 侧出现真实 RL runtime owner 后再落接口

这三条线不能继续混在一个子目标里推进。

## Recommended Split

### A. 继续扩现有 `/api/v1/openpi/training/start`

做法：直接给当前 request 增加更多字段，让 low-level bridge 同时承担 generic training 和 Mint-native SFT。

问题：

- 现有 generic bridge contract 会不断膨胀
- SDK 无法区分 low-level bridge 和 higher-level SFT surface
- 后续 RL 很容易继续塞进同一个 endpoint，训练语义再次混乱

### B. 保留 generic bridge，新增 isolated SFT route

做法：保留 `/api/v1/openpi/training/start` 不动，新增 `/api/v1/openpi/training/sft/start` 和对应 SDK method。SFT request 以 OpenPI template config 为 anchor，再通过 `config_overrides` 白名单显式覆盖常用训练超参。

结论：选 B。

原因：

- 不破坏现有 deterministic contract 和已有 SDK/client 行为
- OpenPI SFT lane 和 future RL lane 可以在 route / type / docs 上保持独立
- 实现上仍然复用 `src/openpi` 已有 dataclass/runtime surface，而不是再造一套训练 DSL

### C. 直接做 SFT + RL 双接口

当前不成立，因为 `src/openpi` 还没有可复用的 RL runtime facade。Mint 侧先做 RL 接口只能制造伪 owner。

## SFT Contract Shape

### Route family

- 保留：`POST /api/v1/openpi/training/start`
- 新增：`POST /api/v1/openpi/training/sft/start`

### Request shape

SFT request 采用 “config family anchor + top-level override whitelist”：

- `config_name`
- `exp_name`
- `backend`
- `overwrite`
- `resume`
- `config_overrides`
  - `batch_size`
  - `num_train_steps`
  - `log_interval`
  - `save_interval`
  - `keep_period`
  - `wandb_enabled`
  - `seed`

### Mapping rule

- `config_name` 仍然指向 `src/openpi/src/openpi/training/config.py` 的现有 config entry
- Mint 只对该 template 的白名单顶层字段进行显式 override
- 任何不在白名单中的 override 都直接返回 422
- Mint 继续持有 `checkpoint_base_dir`、`exp_name`、`overwrite`、`resume`
- v1 不通过 HTTP 传输 `model`、`data`、`weight_loader`、`optimizer` 或 `lr_schedule` 这类复杂内部对象

### Result shape

- start response 使用独立 type：`openpi_sft_training_start`
- future resolved payload 使用独立 type：`openpi_sft_training_result`
- run URI 独立到 `mint://openpi/sft/<config>/<exp>`

## Non-Goals For This Batch

- 不暴露 OpenPI `TrainConfig` 的全部字段
- 不把 Mint 变成 OpenPI dataset / weight-loader / optimizer authoring layer
- 不把 RL rollout / reward / policy loss 语义塞进 SFT endpoint
- 不在这批实现里解决 remote deployment owner、stable base URL 或 real checkpoint fixture

## Validation Strategy

- repo-local Mint contract tests
- repo-local Toolkit SDK tests
- cross-repo fake-runtime closed loop
- localhost live-service smoke
- `git diff --check`

远端部署 smoke 继续留在 `ST-08`，不作为这批代码实现的前置条件。
