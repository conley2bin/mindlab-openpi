# ST-01 Integration Boundaries And Contracts

## Current Status

- Status: drafted

## Objective

为 OpenPI 接入 Mint 建立长期稳定的边界定义和共同语言，确保后续所有实现都在同一组约束下推进，而不是在仓库之间各自形成隐含假设。

## Why This Exists

当前三仓的历史角色不同：

- `src/mint` 是以 Tinker-compatible 服务为中心的服务端仓库。
- `src/openpi` 是以研究代码、脚本入口和模型实现为中心的模型仓库。
- `src/mindlab-toolkit` 当前主要是 MinT 对 Tinker SDK 的兼容包装。

如果不先固定边界，后续最容易发生两类偏移：

- 把 OpenPI 私有能力伪装成 upstream `tinker` 兼容接口，导致语义混乱。
- 把同一份逻辑分别复制到 `mint`、`openpi`、`mindlab-toolkit`，造成长期维护成本失控。

## Repositories In Scope

- `src/mint`
- `src/openpi`
- `src/mindlab-toolkit`

## Current Topology Signals

- `src/mint` 当前围绕 `tinker_server` 组织，对外主语义仍是 Tinker-compatible service。
- `src/openpi` 当前同时包含模型实现、训练逻辑、serving 入口、脚本工作流与 `openpi-client` 包，说明它既是研究仓库，也是未来运行时语义的唯一来源候选。
- `src/mindlab-toolkit` 当前通过顶层 `mint.*` re-export 和 `mint.tinker.*` 兼容层对外提供 MinT 名称空间，说明外部契约已经存在，不能在 OpenPI 接入时被隐式改写。
- 三仓现状不是“一个主仓加两个薄封装”，而是三种历史抽象叠加后的并存状态，因此边界定义必须先于具体接入工作。
- 这些 topology signals 只用于识别当前冲突面，不意味着后续必须冻结内部目录结构。

## Current Semantic Friction

- `src/mint/tinker_server/models/types.py` 当前主请求模型围绕 token/chunk、sampling session、logprobs 与训练 model 创建语义组织。
- `src/openpi/packages/openpi-client/src/openpi_client/base_policy.py` 与 websocket client/server 当前围绕 `obs -> action` 调用语义组织，而不是 token continuation。
- `src/openpi/packages/openpi-client/src/openpi_client/image_tools.py` 说明 OpenPI 客户端路径天然包含图像预处理与多模态 payload，而不是纯文本 token-only 输入。
- `src/openpi/packages/openpi-client/src/openpi_client/base_policy.py` 与 runtime 相关代码同时暴露 `reset()` 语义，说明 OpenPI policy 生命周期不应被简单等同为一次无状态采样请求。
- 因此，OpenPI 接入 Mint 时真正需要解决的是“语义面和生命周期面都不一致”，不是“给现有 token-only 接口再加几个字段”。

## Planned Direction

- 明确 OpenPI 在 Mint 中的定位：Mint 内独立子系统，而非 upstream `tinker` 原协议扩展。
- 固定命名边界：服务端、SDK、工件、会话、训练运行时都使用显式 OpenPI 语义，不和现有 Tinker-compatible 语义混名。
- 固定仓库职责：
  - `src/openpi` 负责模型运行时与工件语义。
  - `src/mint` 负责服务编排、生命周期与平台集成。
  - `src/mindlab-toolkit` 负责用户接口与默认体验。
- 固定兼容边界：OpenPI 接入不得改变现有 Mint 模型路径和当前顶层 `mint.*` 默认行为。
- 固定演进边界：优先支持推理与监督式适配；RL 只保留演进空间，不作为此阶段前置承诺。

## Contract Axes

- 协议边界：OpenPI 相关 API 不伪装成 upstream `tinker` 原协议扩展。
- 命名空间边界：`mint.openpi.*`、Mint 内 OpenPI service surface、OpenPI runtime object 应保持显式命名。
- 工件边界：checkpoint、训练输出、会话产物与元数据的归属语义必须清晰区分于现有 Mint 模型路径。
- 生命周期边界：模型加载、推理会话、监督式适配任务与后续更复杂训练流程必须有一致的对象语义。
- 仓库职责边界：模型私有语义留在 `src/openpi`，平台承载留在 `src/mint`，用户入口留在 `src/mindlab-toolkit`。
- 版本边界：跨仓外部契约必须存在显式版本演进策略，避免三仓靠同一时间发布来维持兼容。

## Naming And Surface Rules

- 用户入口规则：Mint 用户显式通过 `mint.openpi.*` 使用 OpenPI 能力，不通过修改现有 `mint.*` 顶层默认导出完成接入。
- 服务入口规则：Mint 内 OpenPI API 应处于独立的 OpenPI service family，而不是直接复用现有 Tinker-compatible route family 的同名语义。
- 运行时规则：`src/openpi` 对外暴露的是 OpenPI runtime / policy / training / artifact 语义，而不是 Tinker-compatible sampling 语义包装层。
- 对象命名规则：凡是只对 OpenPI 成立的对象，都应保留 OpenPI 前缀或独立命名空间，避免与现有 `session`、`model`、`sampling` 等通用名发生语义漂移。

## Contract Ownership Model

- `src/openpi` 持有 OpenPI runtime 的 canonical semantic contract：policy 输入输出语义、训练状态语义、artifact 语义、模型侧错误语义。
- `src/mint` 持有 Mint service contract：服务端请求响应 envelope、任务编排、鉴权、轮询、平台 metadata 与运维可见性。
- `src/mindlab-toolkit` 持有 SDK contract：用户如何在 `mint.openpi.*` 下稳定访问 Mint 已公开的 OpenPI service surface。
- 如果某类契约同时涉及模型语义和服务传输语义，应以 `src/openpi` 定义语义对象，以 `src/mint` 定义服务包装，不应让两边各自产生一份 canonical definition。

## Boundary Violation Examples

- 如果 Mint 为了复用现有 `/api/v1` 路径，把 OpenPI 私有输入语义伪装成现有 Tinker-compatible request shape，属于协议边界违规。
- 如果 Toolkit 通过修改当前顶层 `mint.ServiceClient` 默认行为来偷偷接入 OpenPI，属于命名空间边界与兼容边界违规。
- 如果 Mint 为了赶进度复制 OpenPI 的 checkpoint、LoRA 或训练状态逻辑到服务端仓库，属于仓库职责边界违规。
- 如果 OpenPI runtime 的外部行为变化没有伴随兼容策略，只要求 Mint 与 Toolkit 同步修改，属于版本边界违规。
- 如果后续方案试图把 OpenPI 的 observation/image/action 语义压扁成 token prompt / sampled sequence，只为了复用现有 Tinker-compatible schema，属于协议边界与生命周期边界违规。
- 如果后续方案忽略 OpenPI policy 的 `reset()` / runtime lifecycle，仅把它当成普通无状态文本采样器对接，属于生命周期边界违规。

## Expected Outcomes

- 后续子目标使用同一套术语描述对象边界。
- OpenPI 相关接口不会与现有 Tinker-compatible 接口发生语义混淆。
- 三仓之间不会因为职责不清而长期互相复制逻辑。

## Non-Goals

- 修改 `src/tinker`
- 追求 upstream `tinker` 原协议完全兼容
- 通过 monkey-patch 或隐式复用让现有顶层 `mint.*` 改变语义
- 在边界尚未稳定前承诺完整 RL 方案

## Dependencies

### Upstream

- 无

### Downstream

- `ST-02 OpenPI Runtime Surface`
- `ST-03 Mint OpenPI Service Plane`
- `ST-04 Mindlab Toolkit OpenPI SDK`
- `ST-05 Cross-Repo Validation And Compatibility`

## Guidance For Later Subtargets

- 后续子目标如需新增目录、接口或工件格式，必须先落在本子目标定义的边界内。
- 任何“为了快先复用现有 Tinker-compatible 路径”的方案，都应视为例外而不是默认方向。
- 后续若要扩展至更广的 `pi0` 家族或更复杂训练路径，应优先复用本子目标沉淀的术语和契约。
