# Root Mint Ops Skills Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把主仓库 `.codex/skills` 从 `src/mint/.claude/skills/*` 的引流包装器重写成 owning skills，并把 dev server、Volcano/Ray、Unison sync、namespace isolation 的当前约束沉淀为主仓库真相。

**Architecture:** 保留 `mint-dev` 与 `volcano-cluster` 作为高频入口，但不再引用 `src/mint` 子模块 skill。新增 `mint-sync-unison` 与 `ray-namespace-isolation` 两个 root skill，把 code sync、per-user PFS、Ray namespace、显式 `RAY_ADDRESS`、本地 raylet attach 与 generic queue control-plane 验证拆开。相关 ST-08 目标/计划/进度文档同步吸收新的主仓库入口和当前环境信号。

**Tech Stack:** Markdown skills, reference templates, docs/targets, docs/plans, docs/progress

---

## Task 1: Freeze The Current Operational Facts

**Files:**
- Create: `docs/plans/2026-03-13-root-mint-ops-skills.md`
- Modify: `docs/progress/openpi-validation-baseline.md`

**Steps**

1. 记录当前 `mint-dev` / Volcano / Ray / Unison 的已验证事实。
2. 明确哪些事实来自仓库技能，哪些事实来自实际只读探测。
3. 把环境特定风险写进 progress，而不是只留在会话里。
4. 记录远端 healthz、`address="auto"`、`volc ml_task` 三类命令在哪些主机上真实可用，避免把错误探测路径写成 canonical SOP。
5. 记录 `healthz ready` 不能单独代表 detached queue actor healthy，远端最短验证链还需要 `debug_state`、`noop` 和 `retrieve_future`。

## Task 2: Replace Wrapper Skills With Owning Root Skills

**Files:**
- Modify: `.codex/skills/mint-dev/SKILL.md`
- Modify: `.codex/skills/volcano-cluster/SKILL.md`

**Steps**

1. 删除“去 `src/mint/.claude/skills/*` 继续读”的包装行为。
2. 让 `mint-dev` 直接拥有 dev host、server、healthz、日志、显式 `RAY_ADDRESS`、只读排查流程。
3. 让 `volcano-cluster` 直接拥有 head/worker 生命周期、queue 选择、CLI caveat、Ray head IP 获取与集群验证流程。
4. 在 skill body 中只引用主仓库 `.codex/skills/*` 下的新 references，不再依赖 `src/mint`.

## Task 3: Add Root Skills For Sync And Namespace Isolation

**Files:**
- Create: `.codex/skills/mint-sync-unison/SKILL.md`
- Create: `.codex/skills/mint-sync-unison/references/volcano-tinker.prf`
- Create: `.codex/skills/ray-namespace-isolation/SKILL.md`
- Create: `.codex/skills/volcano-cluster/references/mint-dev-head.yaml`
- Create: `.codex/skills/volcano-cluster/references/mint-dev-worker.yaml`

**Steps**

1. 把本机 Unison daemon、per-user PFS root、remote `.git` 不存在、server symlink 消费 PFS 这些事实拆成独立 skill。
2. 把 `ssh mint-dev` 落在 `root`、不能用 remote `$USER` 推断 PFS owner、必须从 `/root/tinker_project/tinker-server` symlink 解析实际 PFS root 这条约束写进 skill。
3. 把 `TINKER_RAY_NAMESPACE`、`MINT_RAY_NAMESPACE`、`PFS_TINKER_PATH`、显式 `RAY_ADDRESS` 约束拆成独立 skill。
4. 在 root `volcano-cluster` 下放参考版 head/worker YAML，修正 worker 模板继续指向共享 `/vePFS-Mindverse/share/code/tinker-server` 的问题，改成显式 per-user / placeholder 形式。

## Task 4: Sync ST-08 Documentation

**Files:**
- Modify: `docs/targets/subtarget-08-remote-deployment-and-real-checkpoint-validation.md`
- Modify: `docs/plans/st-08-remote-deployment-and-real-checkpoint-validation.md`
- Modify: `docs/progress/openpi-validation-baseline.md`

**Steps**

1. 在 target 中把主仓库 root skills 写成 remote validation 和 dev environment 的 canonical entry。
2. 在 plan 中增加 root skill deliverables 与 operational baseline 约束。
3. 在 progress 中记录当前环境事实：
   - `mint-dev` 主机无本地 GPU
   - `ray.init(address="auto")` 可能指向 stale head
   - 显式 `RAY_ADDRESS` 才能稳定绑定当前活跃 dev head
   - `mint-dev` host-local driver 需要先附着本地 CPU-only raylet
   - detached queue actor 需要 control-plane headroom，且 remote validation 不能只看 healthz
   - Unison 主动端在本机，不在 `mint-dev`

## Task 5: Validate Skills And Doc Consistency

**Files:**
- Validate: `.codex/skills/mint-dev`
- Validate: `.codex/skills/volcano-cluster`
- Validate: `.codex/skills/mint-sync-unison`
- Validate: `.codex/skills/ray-namespace-isolation`

**Steps**

1. 运行 `quick_validate.py` 检查新旧 root skill 的 frontmatter 和结构。
2. 按 `sync-target-docs` 规则检查 `docs/targets/` 结构一致性。
3. 手动检查技能与文档互相引用是否仍指向 `src/mint/.claude/skills/*`。
4. 用只读环境复核关键命令是否对应当前现实，特别是远端 healthz 探测、显式 `RAY_ADDRESS` 约束，以及 Volcano CLI 的 host 依赖。
