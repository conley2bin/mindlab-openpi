# ST-05 Cross-Repo Validation And Compatibility

## Current Status

- Status: drafted

## Objective

建立 OpenPI 接入 Mint 的跨仓验证、兼容边界与演进机制，确保新能力可以持续推进，同时不破坏现有 Mint 模型路径和当前 SDK 兼容承诺。

## Why This Exists

OpenPI 接入不是单仓改动，而是三仓联动：

- `src/openpi` 提供运行时语义
- `src/mint` 提供服务端承载
- `src/mindlab-toolkit` 提供用户入口

如果没有跨仓验证和兼容策略，最容易出现的问题不是“某一处代码写错”，而是：

- 三仓各自演进后接口漂移
- 新增 OpenPI 能力时回归现有 Mint 模型路径
- SDK 与服务端语义不一致
- 工件格式、命名和生命周期逐步分叉

## Repositories In Scope

- `src/mint`
- `src/openpi`
- `src/mindlab-toolkit`

## Current Topology Signals

- `src/mint/tests` 已经存在大量针对路由语义、checkpoint 行为、gateway 代理、健康检查与调度边界的回归测试。
- `src/openpi` 当前测试分散在 `src/openpi/src/openpi/**/*_test.py`、`src/openpi/scripts/train_test.py` 与 `src/openpi/packages/openpi-client/src/openpi_client/*_test.py`，说明 runtime、脚本与客户端语义目前并未被单一路径统一约束。
- `src/mindlab-toolkit/tests/test_namespace_contract.py` 与 `test_mint_polling_patch.py` 说明 Toolkit 最脆弱的点是外部契约漂移，而不是内部算法正确性。

## Planned Direction

- 为 OpenPI 接入建立明确的回归边界：现有 Mint 模型路径、现有 Tinker-compatible SDK 行为、现有默认 API 语义都必须可验证。
- 建立跨仓最小闭环验证思路，覆盖至少：
  - OpenPI runtime 到 Mint service 的调用边界
  - Mint service 到 Toolkit SDK 的调用边界
  - 关键工件与元数据的一致性
- 明确区分三类验证信号：OpenPI 新能力可用、现有 Mint 主路径未回归、现有 Toolkit 兼容层未漂移。
- 验证分层至少应包括：OpenPI runtime contract、Mint service contract、Toolkit namespace contract、跨仓端到端闭环。
- 跨仓验证必须覆盖 OpenPI 特有的结构化 observation / action / multimodal payload，而不只是“请求能发出去、任务能轮询回来”。
- 兼容验证必须覆盖“现有 token-only 路径未被污染”这一反向信号，否则很容易只验证到新路径可用。
- 让验证体系不仅覆盖“能否工作”，还覆盖“是否污染现有路径”。
- 跨仓验证需要同时考虑版本组合与发布节奏，不能默认三仓永远以同一提交窗口联动发布。
- 持续集成策略应支持单仓自检与跨仓联调两类入口，否则兼容问题会在集成末端才暴露。
- 为后续更广的 `pi0` 家族支持、更多训练模式、甚至更晚的 RL 扩展保留兼容演进机制。
- 把验证与兼容策略作为长期机制维护，而不是上线前一次性补充。

## Expected Outcomes

- OpenPI 接入主线具备跨仓一致的健康检查方式。
- 现有 Mint 模型族与现有兼容 SDK 具备明确回归防线。
- 后续扩展新能力时，可以在既有兼容边界内增量演进。

## Non-Goals

- 在尚未稳定的阶段承诺完整 RL 能力
- 通过跳过验证换取接入速度
- 让验证逻辑长期停留在人工口头约定层面

## Dependencies

### Upstream

- `ST-01 Integration Boundaries And Contracts`
- `ST-02 OpenPI Runtime Surface`
- `ST-03 Mint OpenPI Service Plane`
- `ST-04 Mindlab Toolkit OpenPI SDK`

### Downstream

- 无

## Guidance For Later Subtargets

- 每次新增 OpenPI 能力时，都应先判断它是否改变了既有兼容边界，再决定验证范围。
- 验证体系应覆盖“OpenPI 新能力可用”和“旧能力未受影响”这两类信号。
- 未来如果需要纳入 RL 或更复杂训练流程，也应优先扩展本子目标下的兼容机制，而不是跳过它。
- 如果某次变更只能通过放宽现有 Tinker-compatible 测试断言才能通过，应先把它视为路径污染风险，而不是默认接受的新兼容行为。
