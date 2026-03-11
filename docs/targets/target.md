# OpenPI Integration Into Mint Target

## Goal

本目标用于定义将 OpenPI 的 `pi0` 系列模型接入 Mint 的长期发展方向。

目标不是追求对 upstream `tinker` 协议的字面兼容，也不是用临时补丁把 OpenPI 硬塞进现有 LLM 路径。目标是在不修改 `src/tinker` 的前提下，在 Mint 内建立一个能够长期演进的 OpenPI 子系统，使 `src/mint`、`src/openpi`、`src/mindlab-toolkit` 之间的职责边界稳定、接口语义清晰、后续扩展可持续。

## Target State

- Mint 内存在独立的 OpenPI service surface，与现有 Tinker-compatible 路径并存，但不改变后者语义。
- OpenPI 对 Mint 暴露稳定的库级运行时接口，而不是仅通过脚本入口集成。
- Mindlab Toolkit 通过 `mint.openpi.*` 暴露显式的 OpenPI 客户端能力，而不是隐式改写现有顶层 `mint.*` 行为。
- `pi0` 家族的推理与监督式适配具备清晰的生命周期管理、工件边界和兼容策略。
- 现有 Mint 模型族与当前 Tinker-compatible 用户路径保持稳定，不因为 OpenPI 接入而回归。

## Scope

### In Scope

- `src/mint`
- `src/openpi`
- `src/mindlab-toolkit`

### Out Of Scope

- 修改 `src/tinker`
- 追求 upstream `tinker` 原协议的完全兼容
- 为了接入 OpenPI 而整体重写 Mint 现有模型栈
- 在目标阶段承诺完整 RL 方案
- `docs/targets` 文档治理流程或自动同步 skill 的建设

## Long-Term Constraints

1. `src/tinker` 不在修改范围内，OpenPI 接入不得以修改 upstream 协议为前提。
2. OpenPI 必须作为 Mint 内独立子系统接入，不能伪装成现有 Tinker-compatible 路径的同构实现。
3. 现有 Mint 模型路径、现有 `/api/v1` 语义、现有默认客户端行为必须保持稳定。
4. 可复用的 OpenPI 逻辑应沉淀在 `src/openpi`，不能长期复制到 `src/mint` 或 `src/mindlab-toolkit`。
5. 用户入口必须显式区分 OpenPI 能力，避免让不同协议语义共享同名接口。
6. OpenPI runtime、Mint service surface、Toolkit SDK 之间的外部契约变更必须有显式版本演进与兼容策略，不能依赖隐式同步。

## Planning Principles

- 优先建立稳定边界，再扩展能力深度。
- 优先提炼可复用运行时接口，再做服务端接入和客户端封装。
- 目标文档保持长期视角，不用阶段性赶工目标污染总目标。
- 子目标文档负责细化方向和约束，不在此处下沉到逐文件任务拆分。

## Repository Roles

| Repo | Role |
| --- | --- |
| `src/mint` | 服务端落地，承接 OpenPI 子系统的 API、会话、工件、调度与集成边界 |
| `src/openpi` | 模型与训练运行时核心，提供 Mint 可调用的稳定库接口 |
| `src/mindlab-toolkit` | 面向 MinT 用户的 OpenPI 客户端封装、命名空间与默认配置 |

## Validation Ownership

- `src/openpi` 负责运行时语义与模型私有行为的正确性边界。
- `src/mint` 负责服务端行为、资源隔离、失败隔离与既有路径不回归的边界。
- `src/mindlab-toolkit` 负责用户入口、命名空间和兼容封装的契约边界。
- 跨仓接口一致性与最小闭环验证由 `ST-05` 统一约束，不能默认落到单仓自证。

## Coverage Notes

- `src/openpi` 不只包含模型定义，还包含 `src/openpi/src/openpi/{policies,training,serving}` 与 `src/openpi/packages/openpi-client`；目标拆分必须同时覆盖运行时语义、现有 serving 入口与客户端复用边界。
- `src/mint` 不只包含 `tinker_server/{routes,backend,models}`，还包含 `app.py`、`config.py`、`gateway.py`、`checkpoints.py`、`tests/` 与 `configs/`；OpenPI 接入文档不能把服务端工作误收缩成“只改路由”。
- `src/mindlab-toolkit` 当前代码量很薄，但顶层 `mint` 命名空间、`mint.tinker` 兼容层与 `tests/test_namespace_contract.py` 实际上构成了最硬的外部契约面。
- 因此，子目标拆分按能力边界而不是按目录层级组织：运行时接口、服务平面、SDK 命名空间、跨仓验证分别承接这些结构面。

## 子目标总表

| ID | Name | Status | Repos | Focus | Doc |
| --- | --- | --- | --- | --- | --- |
| ST-01 | Integration Boundaries And Contracts | completed | `src/mint`, `src/openpi`, `src/mindlab-toolkit` | 固定长期边界、命名、协议定位与工件契约 | [subtarget-01-boundaries-and-contracts.md](./subtarget-01-boundaries-and-contracts.md) |
| ST-02 | OpenPI Runtime Surface | completed | `src/openpi` | 将脚本式能力整理为 Mint 可调用的稳定运行时接口 | [subtarget-02-openpi-runtime-surface.md](./subtarget-02-openpi-runtime-surface.md) |
| ST-03 | Mint OpenPI Service Plane | completed | `src/mint` | 在 Mint 内建立隔离的 OpenPI 服务平面与生命周期管理 | [subtarget-03-mint-openpi-service-plane.md](./subtarget-03-mint-openpi-service-plane.md) |
| ST-04 | Mindlab Toolkit OpenPI SDK | completed | `src/mindlab-toolkit` | 提供显式 `mint.openpi.*` 客户端能力并保持现有兼容层稳定 | [subtarget-04-mindlab-toolkit-openpi-sdk.md](./subtarget-04-mindlab-toolkit-openpi-sdk.md) |
| ST-05 | Cross-Repo Validation And Compatibility | completed | `src/mint`, `src/openpi`, `src/mindlab-toolkit` | 建立跨仓验证、兼容边界与后续演进机制 | [subtarget-05-cross-repo-validation-and-compatibility.md](./subtarget-05-cross-repo-validation-and-compatibility.md) |

## Dependency Notes

- `ST-01` 提供全局边界和术语基线，后续子目标都依赖它的结论。
- `ST-02` 和 `ST-03` 共同构成服务端能力核心，但 `ST-02` 应优先于大规模服务端落地。
- `ST-04` 依赖 `ST-02` 与 `ST-03` 的稳定接口，不应提前固化用户接口。
- `ST-05` 贯穿整个主线，用于避免 OpenPI 接入过程侵蚀现有 Mint 路径。
