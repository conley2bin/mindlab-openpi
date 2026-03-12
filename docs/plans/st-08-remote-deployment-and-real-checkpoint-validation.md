# ST-08 Remote Deployment And Real-Checkpoint Validation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立 localhost 之外的 remote deployment smoke 和服务托管 real-checkpoint validation layer，并把失败归因口径固定成可维护的制度。

**Architecture:** 保留 deterministic repo-local / localhost lanes 为主 gate。新增的 remote deployment smoke 和 real-checkpoint lane 必须作为独立验证层存在，并显式区分 environment、deployment、runtime、service、SDK 五类失败来源。

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

## Deliverables

- `src/mint/tests/test_openpi_remote_deployment_smoke.py`
- Updated remote deployment smoke plan
- Updated real-checkpoint validation attribution plan
- Updated progress docs once a concrete lane lands

## Phase 1: Define Remote Deployment Smoke Boundary

**Steps**

1. 定义 remote deployment smoke 与 localhost smoke 的边界。
2. 定义它需要覆盖的最小 OpenPI contract。
3. 定义失败归因 bucket 和不可进入 hard gate 的条件。
4. 落一条 env-driven remote smoke harness，默认不进 hard gate，只在显式 opt-in 时执行。
5. 保证 remote smoke 继续复用 `src/openpi` 已有 remote-serving 语义和 Toolkit 已有 `MINT_OPENPI_*` 入口，不额外发明并行配置面。

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
