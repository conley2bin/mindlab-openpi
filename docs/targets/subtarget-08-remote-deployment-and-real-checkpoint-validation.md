# ST-08 Remote Deployment And Real-Checkpoint Validation

## Current Status

- Status: in_progress

## Objective

把 OpenPI 接入的验证层从 localhost deterministic / low-cost lane 继续扩展到 remote deployment smoke 与 real-checkpoint high-cost lane，并明确环境归因口径，避免后续把环境问题、部署问题和 semantic regression 混成同一种失败。

## Why This Exists

当前已经有：

- deterministic repo-local gates
- service-hosted fake-runtime closed loop
- localhost real-HTTP smoke
- service-hosted local checkpoint-layout artifact round-trip

但还没有：

- localhost 之外的 remote deployment smoke
- 服务托管场景下的 real-checkpoint / real-asset 高成本验证层
- 一套把环境、部署、runtime、SDK 失败先分桶再处理的制度化验证面

## Repositories In Scope

- `src/mint`
- `src/openpi`
- `src/mindlab-toolkit`

## Current Topology Signals

- `docs/progress/openpi-validation-baseline.md` 已经把 `policy_test.py` 和 `download_test.py` 冻结为 exploratory lane，也已经新增 `src/mint/tests/test_openpi_remote_deployment_smoke.py` 的 env-driven 远端验证入口。
- `docs/progress/openpi-compatibility-matrix.md` 现在已经把 remote deployment smoke 记成一个 opt-in validation layer，而不是“完全不存在”。
- `src/mint/tests/test_openpi_live_service_smoke.py` 仍只覆盖 localhost transport；远端部署编排和远端 real-checkpoint infer 则由新的 env-driven lane 单独承接。

## Planned Direction

- 单独建立 remote deployment smoke，不直接改写当前 localhost smoke 的定义。
- 单独建立服务托管 real-checkpoint / real-asset lane，不让它反向污染 deterministic gate。
- 每条高成本 lane 都必须先定义 failure attribution bucket，再决定是否能进入 hard gate。
- 第一刀允许 lane 依赖显式 env fixture 和人工选择的远端 deployment，不要求它一开始就具备 CI hard gate 条件。

## Expected Outcomes

- localhost、remote deployment、real-checkpoint 三种验证层不再混淆。
- 高成本 lane 失败时，能先归因为 environment、deployment、runtime、service 或 SDK。

## Non-Goals

- 把高成本 lane 直接升级成 must-pass CI gate
- 在没有归因口径前扩张更多模型家族或训练模式

## Dependencies

### Upstream

- `ST-06 Operational Hardening And Release Discipline`
- `ST-07 Capability Negotiation And Skew Detection`

### Downstream

- 无

## Guidance For Later Subtargets

- 远端 smoke 和 real-checkpoint lane 应该新增验证层，不要复写 deterministic lane 的完成定义。
- 如果某条高成本 lane 仍然无法区分环境失败和 contract regression，它还不具备成为 hard gate 的条件。
- 如果远端 lane 依赖 base URL、API key、checkpoint URI 或 observation fixture，它们必须被写成显式 env 输入，而不是藏在测试代码里。
