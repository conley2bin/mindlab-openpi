# ST-06 Operational Hardening And Release Discipline

## Current Status

- Status: completed

## Objective

在 `ST-05` 已经建立的 deterministic 基线之上，补齐真实 HTTP live-service smoke、real-asset exploratory lane 和 repo/version release discipline，使 OpenPI 接入从“结构正确”进入“可运维演进”。

## Why This Exists

当前主线已经具备：

- `src/openpi` runtime/artifact/training facade
- `src/mint` OpenPI service plane
- `src/mindlab-toolkit` `mint.openpi.*` SDK
- repo-local contract tests
- fake-runtime deterministic cross-repo closed loop

这个子目标固定三类运维约束：

- deterministic fake-runtime lane 不能替代真实 HTTP transport 验证
- real checkpoint / manual lane 必须继续和 deterministic gate 分层
- repo/version discipline 必须写进 workflow 和 progress docs，而不是靠口头约定

## Repositories In Scope

- `src/mint`
- `src/openpi`
- `src/mindlab-toolkit`

## Current Topology Signals

- `src/mint/tests/test_openpi_live_service_smoke.py` 现在已经提供 localhost real-HTTP smoke，覆盖 Toolkit SDK 到 Mint service 的 status、infer、artifact resolve/archive 与 training/future 路径，并额外验证 service-hosted local checkpoint-layout round-trip。
- `src/mint/tests/test_openpi_cross_repo_closed_loop.py` 继续提供 service-hosted fake-runtime deterministic closed loop，说明 live-service smoke 不是替代，而是上层补充。
- `docs/progress/openpi-validation-baseline.md` 现在已经冻结 real-asset exploratory 命令和 release discipline，`src/mindlab-toolkit/.github/workflows/test.yml` 与 `src/mint/.github/workflows/test.yml` 也已经补上，`ST-06` 的首批实施缺口已经闭合。
- `src/openpi/.github/workflows/test.yml`、`src/mint/.github/workflows/test.yml` 和 `src/mindlab-toolkit/.github/workflows/test.yml` 都已经提供 repo-native CI 事实锚点。
- `src/mindlab-toolkit/src/mint/openpi/config.py` 的 request-side capability identity、Mint route family 的 negotiated response signal，以及 SDK 侧的 first-cut skew detection 已经由 `ST-07` 落地；`ST-06` 当前不再承接 capability contract 扩展本身。

## Planned Direction

- 保持 `ST-05` 的 deterministic lane 为主门禁，不让 live-service smoke 反向替代 repo-local contract tests。
- 让 localhost real-HTTP smoke 成为 transport-aware validation layer，继续覆盖 status、infer、artifact resolve/archive、training/future 与 local checkpoint-layout round-trip 这些当前最硬的 public contract。
- 把 real checkpoint/manual lane 明确降级为 exploratory surface，单独记录命令、环境依赖和失败归因。
- 为 Mint、Toolkit 和 cross-repo 组合补 release discipline，至少明确支持的 repo/version 组合、文档更新顺序和 workflow 缺口。
- capability/version negotiation 本身已经转入并完成于 `ST-07`；`ST-06` 继续限定在 transport-aware validation、exploratory lane 和 release discipline。

## Expected Outcomes

- Toolkit 到 Mint 的真实 HTTP transport 至少有一条本地可跑的 smoke lane。
- Toolkit 到 Mint 的 service-hosted local checkpoint-layout artifact round-trip 已被固定成可重复验证的 lane。
- real checkpoint/manual lane 有清晰的 exploratory 归属，不再和 deterministic gate 混淆。
- repo/version 组合变化时，有明确的 matrix 更新和 release discipline，而不是默认三仓同日同步。

## Non-Goals

- 真实生产部署编排
- 在没有服务端协商信号的情况下实现 capability/version skew detection
- 完整 RL 或大规模性能压测矩阵

## Dependencies

### Upstream

- `ST-03 Mint OpenPI Service Plane`
- `ST-04 Mindlab Toolkit OpenPI SDK`
- `ST-05 Cross-Repo Validation And Compatibility`

### Downstream

- 无

## Guidance For Later Subtargets

- live-service smoke 应优先验证真实 HTTP transport，而不是继续复用 ASGI in-process transport。
- service-hosted local checkpoint-layout round-trip 可以继续扩展文件内容断言，但不能拿来替代 remote download / real checkpoint inference lane。
- exploratory real-asset lane 失败时必须先归因为 runtime、service、SDK 或 environment，不能写成笼统的 “OpenPI 集成失败”。
- repo/version discipline 先落文档和 workflow，再考虑 capability negotiation 之类更高影响的 contract 扩展。
- 如果后续需要把 live-service smoke 扩成 remote deployment smoke，应新增验证层，不要直接改写当前 localhost lane 的定义。
