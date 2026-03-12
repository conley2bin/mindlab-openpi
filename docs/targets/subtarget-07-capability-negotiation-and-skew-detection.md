# ST-07 Capability Negotiation And Skew Detection

## Current Status

- Status: completed

## Objective

把 `mint.openpi.*` 当前单侧 request identity 扩成显式的 response-side capability contract，并在 Toolkit SDK 内建立最小 skew detection，避免客户端和 Mint service 在 capability/version 漂移时继续静默工作。

## Why This Exists

`ST-06` 已经把 OpenPI 接入推进到 deterministic transport、artifact round-trip 和 release discipline，但当时还留着一个结构性空洞：

- `src/mindlab-toolkit` 会发送 `X-Mint-OpenPI-Capability`
- `src/mint` 当时还没有回传 negotiated signal
- SDK 当时还不能根据服务端信号判断 capability/version 是否漂移

这意味着当前 capability header 只是 transport identity，不是双边 contract。

## Repositories In Scope

- `src/mint`
- `src/mindlab-toolkit`

## Current Topology Signals

- `src/mindlab-toolkit/src/mint/openpi/config.py` 当前持有 `OPENPI_CAPABILITY_VERSION=0.1`，并把它写进请求头 `X-Mint-OpenPI-Capability`。
- `src/mint/tinker_server/openpi/routes.py` 现在会在 `/api/v1/openpi/status`、`/api/v1/openpi/infer`、`/api/v1/openpi/artifacts/resolve`、`/api/v1/openpi/artifacts/archive`、`/api/v1/openpi/training/start` 和 `/internal/openpi/status` 上返回 `X-Mint-OpenPI-Negotiated-Capability=0.1`。
- `src/mindlab-toolkit/src/mint/openpi/client.py` 现在集中解析 negotiated header；header 存在且 mismatch 时抛 `OpenPIClientError`，header 缺失时保持旧服务兼容。
- `src/mint/tests/test_openpi_runtime_bridge.py` 已经固定 Mint 侧 status / infer header 行为，`src/mindlab-toolkit/tests/test_openpi_sdk_contract.py` 已经固定 SDK 侧 mismatch fail-fast 行为。
- `docs/progress/openpi-compatibility-matrix.md` 已经不再把 response-side negotiated signal 记成缺口；当前剩余缺口转移到 richer capability set 与 `ST-08` 的远端验证层。

## Completion Boundary

- `src/mint` 已经返回 response-side negotiated capability signal，不再停留在“文档里写着应该一致”的约定层。
- `src/mindlab-toolkit` 已经在看到 response-side signal 且版本不匹配时 fail-fast，不再继续吞下漂移。
- 第一刀保持 additive contract：只新增 response header，不改现有 JSON payload 形状。
- 当前完成边界停在单一 version string；更细粒度 capability matrix、feature set 或 generic `retrieve_future` 上的 negotiated signal 仍属于后续扩展，而不是本子目标完成定义的一部分。

## Expected Outcomes

- Mint OpenPI service 对外返回显式 response-side capability signal。
- Toolkit SDK 在 capability/version mismatch 时能抛出可归因的错误。
- 当前 capability contract 已经从“文档里写着应该一致”变成“代码会拒绝不一致”。

## Non-Goals

- 设计完整 capability feature matrix
- 修改 `src/openpi` runtime semantic object
- 把 remote deployment smoke 或 real-checkpoint manual lane 塞进本子目标

## Dependencies

### Upstream

- `ST-04 Mindlab Toolkit OpenPI SDK`
- `ST-06 Operational Hardening And Release Discipline`

### Downstream

- `ST-08 Remote Deployment And Real-Checkpoint Validation`

## Guidance For Later Subtargets

- capability negotiation 先收敛到低成本、可加法演进的 signal，不要一开始就把 release matrix、feature flags 和 remote deployment 混在一起。
- skew detection 应优先落在 SDK 入口，而不是要求每个调用方自己先手工探测 status。
- 如果后续需要从单个 version string 扩成结构化 capability set，应在 Mint service contract 内扩展，不要回退成“只靠 header 命名约定”。
- 如果后续要让 generic `retrieve_future` 也携带 OpenPI-negotiated signal，必须先明确它仍是 Mint 通用 future contract，不能把 OpenPI 协商语义隐式扩散到所有异步任务。
