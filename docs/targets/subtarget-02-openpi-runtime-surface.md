# ST-02 OpenPI Runtime Surface

## Current Status

- Status: drafted

## Objective

将 `src/openpi` 当前以脚本入口和研究代码组织的能力，整理为一组可以被 Mint 长期调用的稳定运行时接口，使服务端接入不必依赖脚本拼装或重复实现 OpenPI 逻辑。

## Why This Exists

当前 `src/openpi` 已经具备推理、策略封装、训练脚本和 checkpoint 处理能力，但这些能力仍偏向：

- 通过 `scripts/serve_policy.py`、`scripts/train.py` 等脚本使用
- 通过 examples 展示用法
- 以研究工作流组织，而不是以外部系统嵌入为优先

如果 Mint 直接以脚本为集成边界，后续会出现：

- 服务端与模型仓之间的耦合不可控
- 同一套运行时逻辑被复制到 `src/mint`
- OpenPI 自身无法形成清晰的可复用 API

## Repositories In Scope

- `src/openpi`

## Current Topology Signals

- `src/openpi/src/openpi/models` 与 `src/openpi/src/openpi/policies` 承载 `pi0` 家族、LoRA 与 policy 语义。
- `src/openpi/src/openpi/training` 已经持有训练配置、checkpoint、数据加载与训练辅助逻辑。
- `src/openpi/src/openpi/serving/websocket_policy_server.py` 代表当前对外 serving 入口仍偏向独立 server 进程。
- `src/openpi/packages/openpi-client` 说明仓库内部已经存在客户端与 runtime 相关封装，后续必须先判断复用边界，不能在 Mint 侧再次平行发明一套客户端语义。
- `src/openpi/packages/openpi-client/src/openpi_client/base_policy.py` 与 websocket client/server 当前以 `obs -> action` 为核心接口，而不是 token continuation。
- `src/openpi/packages/openpi-client/src/openpi_client/image_tools.py` 表明现有客户端链路已经天然包含图像处理与多模态 payload 约束。
- `src/openpi/scripts/serve_policy.py`、`src/openpi/scripts/train.py` 与 examples 说明当前外部使用方式仍偏向脚本工作流。

## Planned Direction

- 为 OpenPI 提炼稳定的高层运行时接口，覆盖至少以下能力域：
  - 模型加载与配置绑定
  - 推理调用
  - 监督式适配所需的训练步与状态管理
  - checkpoint 读写与导出
- Mint 应依赖 `src/openpi` 提供的显式 integration-facing runtime surface，而不是直接绑定任意当前研究类、脚本入口或临时内部 helper。
- 保持 `src/openpi` 作为模型与训练语义的唯一来源，避免 Mint 长期持有 OpenPI 私有逻辑副本。
- 将 Mint 依赖的能力沉淀为库级 API，而不是依赖 CLI、example 或 websocket server 作为唯一入口。
- 评估并明确 `src/openpi/packages/openpi-client`、`src/openpi/src/openpi/serving` 与后续 Mint 接入之间的复用边界，避免重复造客户端或运行时封装。
- 让 LoRA、SFT、checkpoint 读写等已经存在于 OpenPI 内部的语义继续留在 `src/openpi` 侧收敛，而不是在 Mint 侧形成第二套适配语义。
- 对外运行时接口需要明确调用模式、批处理能力边界、长任务状态语义与错误传播边界，但不在此阶段提前固化到具体传输协议。
- 对外运行时接口必须保留 OpenPI 的 observation / action / multimodal 语义，不能为了嵌入 Mint 而退化成 token-only 包装层。
- 首个稳定 runtime surface 应优先覆盖 Mint 接入不可绕过的最小闭环：runtime bootstrapping、policy inference lifecycle、训练入口、checkpoint/artifact 绑定；其余研究便利接口不应自动进入长期契约面。
- OpenPI 内部目录和研究实现可以继续演进，但外部运行时契约不能随着内部重构被动漂移。
- 允许内部实现继续保留研究代码风格，但对外提供稳定、可演进的接口层。
- 对 `pi0`、`pi05`、不同后端实现与后续训练模式预留演进空间，但不在此阶段过早泛化。

## Expected Outcomes

- Mint 可以直接调用 OpenPI 运行时，而不是外部驱动 OpenPI 脚本。
- OpenPI 自身的推理与训练入口边界更清晰。
- 后续服务端与 SDK 的实现都围绕 OpenPI 公开运行时接口演进。

## Non-Goals

- 把 `src/openpi` 变成 Mint 专属仓库
- 为了服务端集成而重写整个 OpenPI 内部结构
- 在运行时接口尚未稳定前承诺完整 RL 训练抽象

## Dependencies

### Upstream

- `ST-01 Integration Boundaries And Contracts`

### Downstream

- `ST-03 Mint OpenPI Service Plane`
- `ST-04 Mindlab Toolkit OpenPI SDK`
- `ST-05 Cross-Repo Validation And Compatibility`

## Guidance For Later Subtargets

- Mint 侧如果需要新增 OpenPI 特定行为，应优先通过 `src/openpi` 新增或整理运行时接口，而不是在 `src/mint` 里复制模型细节。
- OpenPI 的公开运行时接口应尽量围绕语义对象设计，而不是围绕单个脚本参数设计。
- 推理先行是合理路径，但运行时接口不能只为单次推理做窄化设计，必须为后续监督式适配保留稳定扩展位。
- OpenPI 内部错误哪些由 runtime 直接暴露、哪些由上层服务面转换，必须作为接口契约的一部分明确下来，不能留给服务端各自猜测。
- 如果 Mint 需要 token 化、日志化或平台侧 metadata 封装，这些都应作为上层适配行为存在，不能反向定义 OpenPI runtime 的核心接口。
- 如果 OpenPI 内部模型实现频繁变化，变化应首先被 runtime surface 吸收；Mint 不应直接追逐底层类和函数的局部重构。
