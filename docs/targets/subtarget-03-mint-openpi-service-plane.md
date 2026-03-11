# ST-03 Mint OpenPI Service Plane

## Current Status

- Status: drafted

## Objective

在 `src/mint` 内建立 OpenPI 专用服务平面，使 OpenPI 模型能够在 Mint 中获得会话、工件、任务、观测、调度和平台集成能力，同时不侵蚀现有 Tinker-compatible 路径。

## Why This Exists

`src/mint` 当前的主路径围绕现有模型族和 Tinker-compatible API 组织，其训练与采样假设主要面向当前 LLM 栈。OpenPI 的输入语义、模型生命周期和训练目标不同，如果直接挤进现有路径，风险主要是：

- 现有 Mint 模型路径发生回归
- 服务端语义被混淆，难以判断哪些能力属于 OpenPI 私有扩展
- OpenPI 相关资源调度、会话和工件管理失去清晰边界

## Repositories In Scope

- `src/mint`

## Current Topology Signals

- `src/mint/tinker_server/app.py` 负责服务装配与生命周期入口，OpenPI 接入最终一定会影响服务注册层，而不只是单个 route 文件。
- `src/mint/tinker_server/routes` 当前按 service / sampling / training / futures / weights 分面组织，说明现有 API 语义已经围绕 Tinker-compatible 路径固化。
- `src/mint/tinker_server/backend` 当前集中会话、队列、容量、训练、LoRA 与模型注册逻辑，OpenPI 接入不能无约束地继续向这些通用文件平铺私有逻辑。
- `src/mint/tinker_server/gateway.py`、`src/mint/tinker_server/checkpoints.py`、`src/mint/tinker_server/config.py` 与 `src/mint/tinker_server/models/types.py` 共同构成服务端协议、工件与配置边界。
- `src/mint/tinker_server/models/types.py` 当前核心是 token / sampling / training request-response 语义，并不对应 OpenPI 的 observation / action / multimodal 调用模型。
- `src/mint/tests` 与 `src/mint/configs` 已经承载大量稳定性约束，后续 OpenPI 服务面必须有清晰的测试与配置归属。

## Service Contract Shape

- OpenPI service contract 的 canonical service schema 应归属 `src/mint`，因为它承载服务端 envelope、任务编排、鉴权、轮询与平台 metadata。
- 但该 service schema 所包装的语义对象必须来自 `ST-02` 定义的 OpenPI runtime surface，而不是由 Mint 自行重新发明一套模型语义。
- 因此，Mint 侧需要的是 OpenPI-specific service schema family，而不是对现有 Tinker-compatible schema 做局部修补。
- “复用 Mint 基础设施”成立的前提是：复用 transport / orchestration / operations，而不是复用已经绑定 token-only 语义的 canonical request model。

## Planned Direction

- 在 Mint 内为 OpenPI 建立独立服务面，命名、路由和生命周期明确区分于现有 Tinker-compatible API。
- 优先通过新增 OpenPI 专用目录和对象边界落地服务端能力，而不是继续把新逻辑平铺到现有通用 backend / route 文件中。
- 把 OpenPI 服务面的讨论范围明确扩展到 app 装配、配置注册、checkpoint/工件代理、观测与测试归属，而不是把“服务端接入”误解成只新增几条 API。
- 尽量复用 Mint 已有的通用平台能力，例如：
  - 认证与访问控制
  - future / polling 机制
  - 任务排队与容量控制
  - checkpoint 存储与元数据管理
  - 观测、日志与运维入口
- 上述复用以前提成立为条件：只有在资源模型、生命周期语义和失败语义不冲突时才复用，不能把“已有基础设施”误当成“天然适配 OpenPI”。
- 服务面需要为 OpenPI 建立独立 schema family，不能把现有 token-only `models/types.py` 通过别名和可选字段硬扩成 OpenPI canonical contract。
- 避免复用不适合 OpenPI 的现有模型 backend 假设，尤其是与当前 LLM 训练/采样实现强耦合的路径。
- 让 OpenPI 的推理和监督式适配共享同一套服务边界，但允许二者分阶段落地。
- 让 OpenPI 子系统在 Mint 中表现为“共享基础设施上的独立专区”，而不是对现有总路线的隐式分叉。
- OpenPI 服务面必须考虑与现有 Mint 模型共存时的资源隔离、容量治理与失败隔离，避免新子系统拖垮既有服务面。
- 服务面设计必须同时覆盖 OpenPI policy lifecycle 与服务端任务 lifecycle 的映射关系，不能默认二者天然等价。

## Expected Outcomes

- Mint 内出现一套独立、可演进的 OpenPI API 与服务生命周期。
- 现有 Mint 模型路径继续保持稳定。
- OpenPI 的会话、工件和任务在服务端具备可观测、可治理的归属边界。

## Non-Goals

- 把 OpenPI 能力硬塞进现有 `sampling` / `training` 通用语义
- 为 OpenPI 接入而整体重写 `tinker_server`
- 让现有 Mint 模型默认共享 OpenPI 私有路径
- 让现有 token/chunk request schema 充当 OpenPI 的长期 canonical request model

## Dependencies

### Upstream

- `ST-01 Integration Boundaries And Contracts`
- `ST-02 OpenPI Runtime Surface`

### Downstream

- `ST-04 Mindlab Toolkit OpenPI SDK`
- `ST-05 Cross-Repo Validation And Compatibility`

## Guidance For Later Subtargets

- OpenPI 服务面应优先以隔离性和可维护性为目标，而不是以复用现有路由数量为目标。
- 如果某项 Mint 现有基础设施可以无语义污染地复用，应优先复用；如果复用会带来协议伪装或行为歧义，应单独实现 OpenPI 路径。
- 目录层面应让 OpenPI 相关 route、backend、model schema 在 `src/mint` 内可被一眼识别，避免后续继续加深现有平铺结构。
- OpenPI 相关测试、配置与运维信号也应有清晰归属，避免把服务面实现完后再补回归防线。
- 推理、训练、工件和观测的对象模型应在服务端保持统一命名，避免不同场景下出现不同“OpenPI 会话”语义。
- OpenPI 子系统出现故障时，隔离策略必须优先保护现有 Mint 主路径，而不是让两套路径一起退化。
- 如果 Mint 需要桥接现有平台能力与 OpenPI 多模态输入，桥接层应位于 OpenPI 专用服务面内部，而不是回写污染现有 Tinker-compatible schema 树。
- 如果 OpenPI policy reset、episode 边界或 runtime bootstrapping 在服务侧需要显式控制，这些控制面也应属于 OpenPI-specific service family，而不是挤入现有 sampling session 语义。
