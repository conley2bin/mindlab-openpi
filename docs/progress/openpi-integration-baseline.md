# OpenPI Integration Baseline

Baseline date: 2026-03-12

## Scope

这份文档只记录当前代码现实、当前缺口和当前主线起点。它不定义长期目标，也不替代实施方案。

## Repo Reality

| Repo | Current truth | Hard anchors | Missing for integration |
| --- | --- | --- | --- |
| `src/openpi` | 已有 standalone inference、policy 装配、training scripts、checkpoint 逻辑和 `openpi-client`。canonical inference/artifact/training 装配已经收敛进 `src/openpi/src/openpi/integration/{runtime,artifacts,training}.py`。`src/openpi/src/openpi/policies/policy_config.py`、`src/openpi/scripts/serve_policy.py`、`src/openpi/scripts/train.py`、`src/openpi/scripts/train_pytorch.py` 和 `src/openpi/scripts/train_test.py` 都已经转向 integration-facing surface；`src/openpi/src/openpi/__init__.py` 当前只导出稳定 inference/training entry。 | `src/openpi/src/openpi/policies/policy.py`, `src/openpi/src/openpi/integration/runtime.py`, `src/openpi/src/openpi/integration/artifacts.py`, `src/openpi/src/openpi/integration/training.py`, `src/openpi/src/openpi/training/checkpoints.py`, `src/openpi/scripts/serve_policy_test.py`, `src/openpi/scripts/train_test.py`, `src/openpi/scripts/train_adapter_test.py` | 缺口已经从“提炼 OpenPI runtime surface”转移到“让 Mint 和 Toolkit 真正消费这层 surface”，以及后续跨仓验证。 |
| `src/mint` | 当前 public service surface 仍以 Tinker-compatible token/chunk API 为主，但 gated OpenPI plane 已覆盖 status、inference、artifact 和 training start。`src/mint/tinker_server/openpi/{routes,models,backend}.py` 现在承载独立 OpenPI route family、schema family、runtime bridge、artifact proxy 和 training bridge；`src/mint/tinker_server/checkpoints.py` 新增 checkpoint-scoped reference resolution；`src/mint/tinker_server/app.py` 只在 `TINKER_OPENPI_ENABLED=1` 时注册 `/api/v1/openpi/*` 与 `/internal/openpi/*`。`src/mint/tinker_server/openpi/routes.py` 现在还会在当前 OpenPI route family 上返回 `X-Mint-OpenPI-Negotiated-Capability`。`src/mint/tinker_server/models/types.py` 仍只服务于 tinker client compatibility。`src/mint/tinker_server/backend/api_work_queue.py` 当前显式保证 detached queue actor 的 control-plane concurrency 高于 worker 数，在 `active_job_id` 变化时唤醒 stale dequeue consumers，并在复用 named actor 前检查 `stats().protocol_version`，旧 actor 自动回收后再重建。 | `src/mint/tinker_server/app.py`, `src/mint/tinker_server/checkpoints.py`, `src/mint/tinker_server/openpi/routes.py`, `src/mint/tinker_server/openpi/models.py`, `src/mint/tinker_server/openpi/backend.py`, `src/mint/tinker_server/backend/api_work_queue.py`, `src/mint/tests/test_openpi_app_registration.py`, `src/mint/tests/test_openpi_service_contract.py`, `src/mint/tests/test_openpi_runtime_bridge.py`, `src/mint/tests/test_openpi_artifact_proxy.py`, `src/mint/tests/test_openpi_training_contract.py`, `src/mint/tests/test_openpi_cross_repo_closed_loop.py`, `src/mint/tests/test_openpi_live_service_smoke.py`, `src/mint/tests/test_issue_190_checkpoint_archive_auth_signed_url.py`, `src/mint/tests/test_issue_218_gateway_checkpoint_proxy.py`, `src/mint/tests/test_gateway_multi_target_routing.py`, `src/mint/tests/test_client_compat_user_agent.py`, `src/mint/tests/test_tinker_prompt_logprobs_semantics.py`, `src/mint/tests/tests_mock_api_work_queue_scheduler.py` | 缺口已经从 Mint service plane 本体转移到 remote deployment / ops 扩展、高成本 real checkpoint/manual lane，以及更细粒度 capability set 是否继续扩展。 |
| `src/mindlab-toolkit` | 当前 package 已从“只有 patched tinker compatibility layer”扩展成“双命名空间”形态。`src/mindlab-toolkit/src/mint/__init__.py` 仍会先执行 `apply_mint_patches()` 并保持顶层 `mint.*` re-export，但现在已经显式暴露 `mint.openpi.*`。`src/mindlab-toolkit/src/mint/openpi/{config,types,client}.py` 提供独立 OpenPI config/type/client surface，通过显式 HTTP transport 访问 Mint OpenPI service plane；client 会在 response-side negotiated capability header 存在且 mismatch 时 fail-fast，在 header 缺失时保持旧服务兼容。 | `src/mindlab-toolkit/src/mint/__init__.py`, `src/mindlab-toolkit/src/mint/tinker/__init__.py`, `src/mindlab-toolkit/src/mint/mint/__init__.py`, `src/mindlab-toolkit/src/mint/openpi/config.py`, `src/mindlab-toolkit/src/mint/openpi/types.py`, `src/mindlab-toolkit/src/mint/openpi/client.py`, `src/mindlab-toolkit/tests/test_namespace_contract.py`, `src/mindlab-toolkit/tests/test_mint_polling_patch.py`, `src/mindlab-toolkit/tests/test_openpi_namespace_contract.py`, `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py` | 缺口已经从 SDK namespace / transport 本体转移到 remote deployment smoke、高成本 real checkpoint/manual lane，以及是否把当前单一 version string 扩成结构化 capability contract。 |

## Cross-Repo Reality

- 已有一条 deterministic fake-runtime closed loop，从 Toolkit SDK 到 Mint service 再到 fake OpenPI runtime，锚点是 `src/mint/tests/test_openpi_cross_repo_closed_loop.py`。
- 已有 repo-owned compatibility matrix，见 `docs/progress/openpi-compatibility-matrix.md`。
- 目前已经有 deterministic status + inference + artifact + training/future cross-repo closed loop，以及 localhost real-HTTP live-service smoke；real-asset exploratory 命令和 release discipline 也已经写入 progress docs。
- `src/mint/tests/test_openpi_remote_deployment_smoke.py` 现在提供一条 env-driven remote deployment smoke：status 是最小 reachability signal；提供 checkpoint env 后可继续覆盖 artifact/archive；再提供 config/observation env 后可继续覆盖 service-hosted real-checkpoint infer。base URL、timeout 和 observation fixture 解析已固定成 environment gate；远端 HTTP response 失败与本地 SDK-side contract/decode failure 也已分开归因。
- `src/openpi/docs/remote_inference.md` 与 `src/openpi/examples/*/compose.yml` 继续作为 upstream remote-serving 事实锚点；`src/mindlab-toolkit/README.md` 则固定了 `MINT_OPENPI_*` 远端入口的用户面，说明 `ST-08` 不是从零定义远端形状，而是在现有三仓材料上补验证和归因。
- `ST-08` 相关 dev host、Volcano/Ray、Unison sync 与 namespace isolation 入口现在收敛到主仓库 `.codex/skills/{mint-dev,volcano-cluster,mint-sync-unison,ray-namespace-isolation}`；这层 root docs 固定了显式 `RAY_ADDRESS`、per-user PFS 和本机 Unison daemon 这些运维前提，避免把 `src/mint/.claude/skills/*` 当成唯一入口。
- `mint-dev` 上当前 shared-cluster lane 已经补上 generic queue control-plane 验证：不能只看 `/api/v1/healthz`，还要看 `/internal/work_queue/debug_state`、`/internal/work_queue/noop` 和 `/api/v1/retrieve_future`。2026-03-13 对同一个 detached `tinker_api_work_queue` 连续做两次 server-only restart 后，这条链仍然保持通过。
- Mint 当前 OpenPI route family 已返回 `X-Mint-OpenPI-Negotiated-Capability`，Toolkit SDK 在 header 存在且 mismatch 时会 fail-fast，在 header 缺失时保持旧服务兼容。
- 三仓现在都已经有 OpenPI-specific repo-local contract tests；缺口已经从 “有没有 live transport” 转移到 “是否继续扩展 remote deployment smoke、高成本 real checkpoint/manual lane，以及更细 capability contract”。

## Semantic Split Observed Today

- `src/mint` 当前核心语义是 token/chunk、sampling session、training model、future retrieval。
- `src/openpi` 当前核心语义是 observation/action/multimodal payload、policy `infer(obs)`、`reset()`、action chunk。
- `src/mindlab-toolkit` 当前核心语义已经分成两层：`mint.*` / `mint.tinker.*` 兼容层，以及 `mint.openpi.*` 显式 OpenPI service client。

这三套语义今天还没有被一个中间层收敛起来。

## Immediate Gaps By Subtarget

| ST | Current gap |
| --- | --- |
| `ST-01` | baseline、validation baseline 和 glossary 已落地。剩余缺口是持续保持 docs/progress 与 docs/targets 同步，不让 current truth 再次分叉。 |
| `ST-02` | OpenPI runtime/artifact/training facade、脚本 adapter 和 stable export 已落地。剩余缺口不在 `src/openpi` 内部抽象层，而在 `src/mint` / `src/mindlab-toolkit` 的消费与跨仓验证。 |
| `ST-03` | `src/mint` 的 OpenPI service plane 已完成首批目标：config gate、route family、schema family、inference bridge、artifact proxy 和 training start 已落地。剩余 operational hardening 已移交给 `ST-06`。 |
| `ST-04` | `src/mindlab-toolkit` 已有显式 `mint.openpi.*` namespace、独立 config/type/client 和 transport dependency。后续真实 HTTP smoke、real-asset lane 与 release/version discipline 已移交给 `ST-06`。 |
| `ST-05` | compatibility matrix、validation baseline、三仓 repo-local contract tests 与 deterministic fake-runtime closed loop 都已落地。当前只负责 deterministic baseline。 |
| `ST-06` | localhost real-HTTP live-service smoke、service-hosted local checkpoint-layout artifact round-trip、real-asset exploratory 命令、release discipline docs、Toolkit repo-native workflow 和 Mint repo-native workflow 已落地。当前没有仍留在 `ST-06` 内部的实现缺口。 |
| `ST-07` | response-side negotiated capability header 与 SDK 侧 mismatch fail-fast 已落地。后续若继续扩张，只剩把单一 version string 扩成结构化 capability set，以及是否让 generic `retrieve_future` 也返回 OpenPI-negotiated signal。 |
| `ST-08` | env-driven remote deployment smoke 与 optional real-checkpoint infer lane 已落地第一刀，但仍依赖外部部署、凭据、checkpoint 和 observation fixture，尚不能进入 hard gate；相关 `mint-dev` / Volcano / Unison / namespace isolation 操作也已经转到主仓库 root skills 统一约束。 |

## Current Working Cut For The First Implementation Pass

这不是“已经支持”的范围，而是当前文档链收敛后的首批切面。

- 当前跨仓 deterministic closed loop 覆盖 public status probe、inference path、artifact resolve/archive path 和 training/future path，锚点是 `src/mint/tests/test_openpi_cross_repo_closed_loop.py`。
- 首批 deterministic local lane 不依赖真实 checkpoint，使用 fake runtime 或 test double。
- 当前 Mint service cut 已经落在 `src/mint/tinker_server/openpi/routes.py` 的 `/api/v1/openpi/{status,infer,artifacts/resolve,artifacts/archive,training/start}`；其中 status 走 Mint-owned service envelope，inference 通过 fake runtime bridge test double 验证 lifecycle 和错误映射，artifact/training 则通过 checkpoint/future contract tests 固定边界。
- 当前 Toolkit SDK cut 已经落在 `src/mindlab-toolkit/src/mint/openpi/{config,types,client}.py`，通过显式 HTTP client 调用 Mint OpenPI service surface；默认 `User-Agent` 为 `MintOpenPI/Python ...`，不落入现有 Tinker compatibility heuristic，并且 status decoder 已吸收 Mint 当前 `status/capabilities` payload。
- 当前 Toolkit SDK 既发送 request-side `X-Mint-OpenPI-Capability`，也会校验 Mint OpenPI route family 返回的 `X-Mint-OpenPI-Negotiated-Capability`；当 header 存在且 mismatch 时 fail-fast，当 header 缺失时保持旧服务兼容。
- 当前 cross-repo closed loop 通过 service-hosted harness 固定在 `src/mint/tests/test_openpi_cross_repo_closed_loop.py`：Toolkit SDK 发起 status / infer / artifact / training 请求，Mint OpenPI route 包装服务层，fake runtime 返回 deterministic action，local checkpoint dir 提供 deterministic archive，fake future store 覆盖 training future 的 pending / failure / success 分支，并显式验证 status contract、artifact transport、training future envelope 与 `reset()` lifecycle signal。
- 当前 localhost live-service smoke 也固定在 `src/mint/tests/test_openpi_live_service_smoke.py`：Toolkit SDK 通过真实 HTTP 请求触发 Mint 的 checkpoint URI 解析、persistent-cache materialization、artifact resolve 和 tar.gz archive stream，并验证 local checkpoint layout 的文件内容按服务端语义返回。
- 当前 remote deployment smoke 入口已经固定在 `src/mint/tests/test_openpi_remote_deployment_smoke.py`：默认不运行，只有在显式设置远端 base URL 与 opt-in env 时才执行；status 是最小 smoke，artifact/archive 与 service-hosted real-checkpoint infer 依赖额外 env fixture。base URL / timeout / observation env 解析失败属于 environment；远端 HTTP error response 不再被默认归到 `sdk`。
- 首批 real-asset exploratory lane 以 `pi0_aloha_sim` 为代表，因为：
  - `src/openpi/src/openpi/policies/policy_test.py` 当前使用 `pi0_aloha_sim`
  - `src/openpi/scripts/serve_policy.py` 当前对 ALOHA simulator 的默认 checkpoint 也是 `pi0_aloha_sim`
- 首批 local training smoke 继续以 `src/openpi/scripts/train_test.py` 的 `debug` config 为锚点，并且该锚点现在通过 `openpi.integration.training` 进入训练 contract。
- `src/openpi/scripts/train_adapter_test.py` 专门锁住 `scripts/train.py` 和 `scripts/train_pytorch.py` 只做 adapter delegation，不再承载 canonical backend contract。
- `pi05_*` 和 `pi0_fast_*` 当前不进入第一条 Mint closed loop；它们保留在后续兼容矩阵扩展里。

## Risks Already Visible

- 如果先做 Mint route，再做 `src/openpi` facade，Mint 会被迫直接依赖研究期内部对象。
- 如果先做 Toolkit SDK，再做 Mint service contract，SDK 会被迫猜 service schema。
- 如果不把旧路径回归测试固定成门禁，OpenPI 接入很容易通过修改旧断言来“放行”路径污染。
- `openpi.integration.training` 的 JAX resume 路径当前依赖 “resumed state 不做 donation” 这个实现约束；后续如果再次改动 `jax.jit(... donate_argnums=...)`，必须重新验证 `src/openpi/scripts/train_test.py`。
- `src/openpi/scripts/train.py` 和 `src/openpi/scripts/train_pytorch.py` 现在是薄 adapter；后续如果在脚本层重新塞回 backend 逻辑，`src/openpi/scripts/train_adapter_test.py` 应该先失败。
