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
- `src/mint/tests/test_openpi_remote_deployment_smoke.py` 现在已经把 base URL、timeout 和 infer lane 已选中后的 observation input 解析固定成显式 environment gate；同时把远端 HTTP error response 与本地 SDK-side contract/decode failure 分开归因，避免把同一类失败混进 `sdk` bucket。若 observation env 未提供，real-checkpoint infer lane 仍然跳过。
- `src/mint/scripts/tools/openpi_remote_smoke.py` 现在提供 repo-owned runner，把 sample fixture 模板、显式 env 组装和底层 pytest 入口收敛到同一个脚本，而不是继续要求手工拼装长串命令。
- 仓库当前已经提供 `src/mint/tests/fixtures/openpi_remote_observation.sample.json` 作为 remote infer 的 sample 模板；测试既支持 `MINT_OPENPI_REMOTE_OBSERVATION_JSON`，也支持 `MINT_OPENPI_REMOTE_OBSERVATION_PATH` 指向绝对路径 fixture。
- `mint-dev` 上已经验证出一条 generic service control-plane 基线：`/api/v1/healthz` ready 不能单独证明队列可用；至少还要通过 `/internal/work_queue/debug_state`、`/internal/work_queue/noop` 和 `/api/v1/retrieve_future`。
- `src/openpi/docs/remote_inference.md` 已经定义 upstream remote policy server / client 的基本形状，`src/openpi/examples/{aloha_real,aloha_sim,libero,simple_client}/compose.yml` 也已经给出服务托管部署样例；`ST-08` 不应无视这些现成锚点重新发明 remote deployment 语义。
- `src/mindlab-toolkit/README.md` 已经把 `MINT_OPENPI_*` 作为远端 OpenPI client 的默认入口；`ST-08` 的 remote smoke 和 real-checkpoint lane 应继续复用这套入口，而不是再造一套单独配置面。
- 主仓库 `.codex/skills/{mint-dev,volcano-cluster,mint-sync-unison,ray-namespace-isolation}` 现在承接 dev host、Volcano/Ray、code sync 与 namespace isolation 的 agent 入口；`src/mint/.claude/skills/*` 可以继续作为参考，但不再是主仓库工作流的唯一入口。
- 当前 cluster discovery 不能假定 `mint-dev` 或 repo host 自带可用 `volc ml_task`；后续实现必须允许 Volcano console 或另一个已配置 CLI host 提供 head/task 发现信息。

## Planned Direction

- 单独建立 remote deployment smoke，不直接改写当前 localhost smoke 的定义。
- 单独建立服务托管 real-checkpoint / real-asset lane，不让它反向污染 deterministic gate。
- 每条高成本 lane 都必须先定义 failure attribution bucket，再决定是否能进入 hard gate。
- 远端 transport 已经成功返回 HTTP response 时，不要把失败默认归到 `sdk`；`sdk` bucket 只保留给本地 client-side decode、capability enforcement 或其他非 HTTP 响应路径的错误。
- 第一刀允许 lane 依赖显式 env fixture 和人工选择的远端 deployment，不要求它一开始就具备 CI hard gate 条件。
- 后续所有需要触达 `mint-dev`、Volcano、Ray、Unison 的实现工作，都应先在主仓库 root skills 里固定入口和约束，再决定是否同步回 `src/mint/.claude/skills/*`。

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
- 如果失败来自远端 HTTP surface 的 status code，它应该先落在 deployment / runtime / service 中的一个；只有 transport 已经成功且本地 client 在 decode 或 capability 校验阶段拒绝响应时，才应归到 `sdk`。
- 如果 remote lane 复用 `mint-dev` shared-cluster 环境，它必须先通过 generic queue control-plane probes，再把后续失败归因到 OpenPI-specific routes。
- 如果 dev host、cluster discovery、code sync 或 namespace isolation 的操作约束发生变化，应先更新主仓库 `.codex/skills/*`，再决定是否同步到 `src/mint/.claude/skills/*`。
