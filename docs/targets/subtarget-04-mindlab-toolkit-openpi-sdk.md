# ST-04 Mindlab Toolkit OpenPI SDK

## Current Status

- Status: completed

## Objective

在 `src/mindlab-toolkit` 中提供显式的 OpenPI 用户入口，使 MinT 用户能够通过统一的 Mint 命名空间使用 OpenPI 能力，同时保持当前 Tinker-compatible 兼容层稳定。

## Why This Exists

`src/mindlab-toolkit` 当前的主要职责是：

- 沿用 `tinker` 的公共客户端对象
- 提供 MinT 名称与默认配置
- 在必要处对 `tinker` 客户端做兼容性 patch

OpenPI 接入后，如果继续把新能力直接塞进现有顶层 `mint.*`，会产生两个问题：

- 用户无法区分哪些接口是 upstream `tinker` 兼容语义，哪些是 Mint 私有 OpenPI 语义
- 兼容层测试与默认行为更容易被悄悄改坏

## Repositories In Scope

- `src/mindlab-toolkit`

## Current Topology Signals

- `src/mindlab-toolkit/src/mint/__init__.py` 当前会在导出顶层符号前应用 patch，并将大量顶层接口直接 re-export 到 `mint.*`。
- `src/mindlab-toolkit/src/mint/tinker` 与 `src/mindlab-toolkit/src/mint/mint` 说明 Toolkit 当前主体仍是“兼容层 + MinT 命名”结构，而不是多协议并列 SDK。
- `src/mindlab-toolkit/src/mint/openpi/{config,types,client}.py` 现在已经形成显式 OpenPI namespace、transport identity 与 decode 边界，说明 SDK surface 已经从计划进入稳定现实。
- `src/mindlab-toolkit/tests/test_namespace_contract.py` 直接锁定了顶层 namespace、re-export 关系与版本语义，说明 OpenPI 接入首先是契约设计问题，其次才是代码量问题。
- `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py` 现在已经锁定 infer、artifact、training start 与 future decode 语义，说明 OpenPI SDK 的主要回归面已经独立存在。

## Current Semantic Friction

- 当前 `mint.*` 顶层导出本质上是对 Tinker-compatible client 对象的 MinT 命名包装。
- OpenPI 现有客户端语义来自 `openpi-client` 的 policy / obs / action / websocket 调用链，而不是 `ServiceClient` / `SamplingClient` 这类 token-centric client 形态。
- 因此，Toolkit 不能把 OpenPI 接入理解成“再导出一组和 tinker 名字相似的 client”，否则用户会误以为两者共享同一协议语义。

## Planned Direction

- 在 Toolkit 中为 OpenPI 提供显式命名空间，例如 `mint.openpi.*`。
- 保持当前顶层 `mint.*` 与 `mint.tinker.*` 的既有语义和兼容约束不变。
- 让 OpenPI SDK 的目录与测试边界显式独立，避免影响当前针对 Tinker-compatible 命名空间的契约测试。
- 把 OpenPI 入口设计成对现有 re-export 结构的显式增量，而不是继续向当前顶层 `__init__` 追加隐式兼容魔法。
- 将用户真正需要的 OpenPI 工作流封装为面向 Mint 的客户端体验，包括：
  - 配置与默认端点
  - 推理调用
  - 训练工作流入口
  - 工件与会话对象的用户可见封装
- 让 Toolkit 承担用户体验统一责任，但不复制 OpenPI 运行时或 Mint 服务端语义。
- Toolkit 需要对 Mint service surface 与 OpenPI runtime 的版本组合给出明确兼容策略，不能默认“三仓一起升级”。
- 对已经直接使用 `openpi-client` 的用户，应保留可迁移而非强制替换的演进空间，避免 `mint.openpi.*` 设计与现有 OpenPI 客户端生态正面冲突。
- `mint.openpi.*` 应反映 OpenPI 自己的对象语义，而不是为了表面一致性去模仿当前 `mint.tinker.*` 的 token-centric 类名与方法名。
- 保持 SDK 对后续 OpenPI 能力扩展友好，不把当前阶段的最小能力错误固化为最终抽象。

## Expected Outcomes

- 用户能够在不混淆协议语义的前提下使用 Mint 内 OpenPI 能力。
- 现有 Tinker-compatible 兼容层测试与行为继续稳定。
- Mint 的 OpenPI 用户入口具有长期可维护性和可读性。

## Non-Goals

- 隐式改写当前顶层 `mint.ServiceClient`、`mint.TrainingClient`、`mint.SamplingClient`
- 把 OpenPI 运行时实现复制到 Toolkit
- 把 Mint 私有 OpenPI 能力伪装成 upstream `tinker` 默认接口

## Dependencies

### Upstream

- `ST-01 Integration Boundaries And Contracts`
- `ST-02 OpenPI Runtime Surface`
- `ST-03 Mint OpenPI Service Plane`

### Downstream

- `ST-05 Cross-Repo Validation And Compatibility`

## Guidance For Later Subtargets

- SDK 设计应优先反映清晰语义，而不是追求表面 API 一致。
- 如需兼容现有用户习惯，应通过显式 wrapper、文档与迁移说明实现，而不是通过隐藏式 monkey-patch 改写行为。
- 命名空间一旦对外发布，后续变更成本很高，因此必须在边界稳定后再固化。
- 任何新增 OpenPI 顶层导出都应先证明不会破坏 `mint.tinker` 与现有 `mint.*` re-export 合约。
- 如果某个 SDK 设计方案需要让用户把 OpenPI observation / image 输入先手工转换成 token prompt 才能调用 Mint，则说明 SDK 抽象已经偏离 OpenPI 主语义。
- `mint.openpi` 可以复用 Mint 的通用 `/api/v1/retrieve_future` 轮询入口，但 OpenPI-specific payload typing、fail-fast drift detection 与 transport identity 仍应留在 `src/mindlab-toolkit/src/mint/openpi` 内处理。
- 如果未来要引入 capability/version skew 检测，应以 Mint OpenPI service 明确返回的协商 signal 为前提，而不是把当前 request-side capability header 误当成双边契约。
