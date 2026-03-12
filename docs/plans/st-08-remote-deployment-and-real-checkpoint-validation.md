# ST-08 Remote Deployment And Real-Checkpoint Validation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立 localhost 之外的 remote deployment smoke 和服务托管 real-checkpoint validation layer，并把失败归因口径固定成可维护的制度。

**Architecture:** 保留 deterministic repo-local / localhost lanes 为主 gate。新增的 remote deployment smoke 和 real-checkpoint lane 必须作为独立验证层存在，并显式区分 environment、deployment、runtime、service、SDK 五类失败来源；其中远端 HTTP error response 不应默认落到 `sdk`，`sdk` bucket 只用于本地 client-side decode / capability enforcement 失败。

**Tech Stack:** FastAPI/HTTP clients, pytest, deployment-specific harness, Markdown

---

## Boundary Inputs

- `docs/progress/openpi-validation-baseline.md`
- `docs/progress/openpi-compatibility-matrix.md`
- `docs/targets/subtarget-08-remote-deployment-and-real-checkpoint-validation.md`
- `src/openpi/docs/remote_inference.md`
- `src/openpi/examples/aloha_real/compose.yml`
- `src/openpi/examples/aloha_sim/compose.yml`
- `src/openpi/examples/libero/compose.yml`
- `src/openpi/examples/simple_client/compose.yml`
- `src/mindlab-toolkit/README.md`
- `.codex/skills/mint-dev/SKILL.md`
- `.codex/skills/volcano-cluster/SKILL.md`
- `.codex/skills/mint-sync-unison/SKILL.md`
- `.codex/skills/ray-namespace-isolation/SKILL.md`

## Deliverables

- `src/mint/tests/test_openpi_remote_deployment_smoke.py`
- `.codex/skills/mint-dev/SKILL.md`
- `.codex/skills/volcano-cluster/SKILL.md`
- `.codex/skills/mint-sync-unison/SKILL.md`
- `.codex/skills/ray-namespace-isolation/SKILL.md`
- Updated remote deployment smoke plan
- Updated real-checkpoint validation attribution plan
- Updated progress docs once a concrete lane lands

## Phase 0: Freeze The Operational Entry Points

**Steps**

1. 把主仓库 root skills 变成 `mint-dev`、Volcano/Ray、Unison sync、namespace isolation 的 owning entry，而不是继续把工作流引流到 `src/mint/.claude/skills/*`。
2. 让 root skills 固定当前已经暴露的环境事实：
   - `mint-dev` 是 driver host，不代表 cluster 本地 GPU 可见性
   - `ray.init(address="auto")` 可能指向 stale head
   - 显式 `RAY_ADDRESS` 必须来自当前活跃 head
   - `mint-dev` host-local driver 需要先让本地 CPU-only raylet 加入当前活跃 shared head
   - code sync 的主动端在本机 Unison daemon，不在 `mint-dev`
   - `ssh mint-dev` 落在 `root`，remote `$USER` 不能当 per-user PFS owner，实际 PFS root 必须从 `/root/tinker_project/tinker-server` symlink 解析
3. 让 worker/reference 模板显式使用 per-user `PFS_TINKER_PATH`，不要再默认共享 `/vePFS-Mindverse/share/code/tinker-server`。
4. 明确 cluster discovery 不能假定 `mint-dev` 或 repo host 都可直接运行 `volc ml_task`；Volcano console 或已配置 CLI host 也是合法 discovery source。
5. 把 `mint-dev` 上的最短 generic service validation 固定下来：`/api/v1/healthz`、`/internal/work_queue/debug_state`、`/internal/work_queue/noop`、`/api/v1/retrieve_future`；healthz ready 不能单独作为 remote smoke 前置条件。

## Phase 1: Define Remote Deployment Smoke Boundary

**Steps**

1. 定义 remote deployment smoke 与 localhost smoke 的边界。
2. 定义它需要覆盖的最小 OpenPI contract。
3. 定义失败归因 bucket 和不可进入 hard gate 的条件。
4. 固定 bucket 边界：environment 负责 env fixture 解析，deployment/runtime/service 负责远端 HTTP surface，SDK 只负责本地 client-side contract enforcement。
5. 落一条 env-driven remote smoke harness，默认不进 hard gate，只在显式 opt-in 时执行。
6. 保证 remote smoke 继续复用 `src/openpi` 已有 remote-serving 语义和 Toolkit 已有 `MINT_OPENPI_*` 入口，不额外发明并行配置面。
7. 保证任何涉及 `mint-dev`、Volcano、Ray、Unison 的操作说明都先收敛到主仓库 root skills，再由测试/文档引用这些入口。

## Phase 2: Define Service-Hosted Real-Checkpoint Lane

**Steps**

1. 定义 real-checkpoint / real-asset lane 的最小成功信号。
2. 定义环境容量、外网下载、模型装配和 SDK/service mismatch 的分桶规则。
3. 明确哪些失败仍然只能算 exploratory，不能算 deterministic regression。
4. 让 remote smoke harness 能在提供 checkpoint/config/observation env 时额外执行 service-hosted real-checkpoint infer。

## Exit Criteria

- remote deployment smoke 的 owner、边界和归因口径明确。
- real-checkpoint high-cost lane 的 owner、边界和归因口径明确。
- progress docs 不再把这两类 lane 混成同一类“OpenPI integration failure”。
