# ST-06 Operational Hardening And Release Discipline Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 deterministic baseline 之上补齐 localhost real-HTTP smoke、service-hosted local checkpoint-layout artifact round-trip、real-asset exploratory lane 和 repo/version release discipline。

**Architecture:** 先补真实 HTTP transport smoke，但仍以 deterministic repo-local 和 fake-runtime closed loop 为主 gate。再补一条 service-hosted local checkpoint-layout artifact round-trip，证明 Mint 的 checkpoint URI 解析、cache materialization 和 archive stream。随后把 real checkpoint/manual lane 明确隔离为 exploratory surface，最后补 repo/version matrix 与 workflow discipline。没有 Mint response-side negotiated signal 之前，不实现 capability/version skew detection。

**Tech Stack:** FastAPI, uvicorn, httpx, pytest, Markdown, repo-local workflows

---

## Boundary Inputs

- `docs/progress/openpi-integration-baseline.md`
- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-validation-baseline.md`

This plan inherits these rules:

- `ST-05` 已经完成 deterministic repo-local gates 和 fake-runtime closed loop。
- `ST-06` 不能用 live-service smoke 取代 repo-local contract tests。
- real-asset/manual lane 必须继续和 deterministic gate 分开。
- capability/version skew detection 只有在 Mint 返回 negotiated response signal 后才进入实现阶段。

## Deliverables

- `src/mint/tests/test_openpi_live_service_smoke.py`
- `src/mint/openpi_testkit.py`
- `src/mint/.github/workflows/test.yml`
- `src/mindlab-toolkit/.github/workflows/test.yml`
- Updated `docs/progress/openpi-integration-baseline.md`
- Updated `docs/progress/openpi-compatibility-matrix.md`
- Updated `docs/progress/openpi-validation-baseline.md`

## Phase 1: Add A Localhost Live-Service Smoke Lane

**Create**

- `src/mint/tests/test_openpi_live_service_smoke.py`
- `src/mint/openpi_testkit.py`

**Modify**

- `src/mint/tests/test_openpi_cross_repo_closed_loop.py`

**Steps**

1. 抽出 Toolkit source-loading、fake runtime、fake future store 和 local test server helper，避免 closed-loop 和 live-service smoke 各自复制一套 harness。
2. 在 Mint 侧启动真实 localhost HTTP server，使用 Toolkit `mint.openpi.OpenPIClient` 走实际 TCP transport。
3. 首批 live-service smoke 至少覆盖：
   - public status
   - inference
   - training start plus retrieve_future
4. 继续使用 fake runtime / fake future store，确保 smoke 证明 transport 和 route registration，而不是引入 real-asset 不确定性。

**Commands**

```bash
cd src/mint && .venv/bin/pytest \
  tests/test_openpi_live_service_smoke.py \
  tests/test_openpi_cross_repo_closed_loop.py -q
```

**Gate**

- 至少一条 Toolkit to Mint localhost real-HTTP lane 存在。
- smoke lane 与 deterministic ASGI closed-loop 共享同一套 contract helper，而不是分叉出第二套语义。

## Phase 2: Add A Service-Hosted Local Checkpoint-Layout Round-Trip

**Modify**

- `src/mint/openpi_testkit.py`
- `src/mint/tests/test_openpi_live_service_smoke.py`

**Steps**

1. 不把 remote download / real checkpoint inference 拉进 deterministic gate。
2. 让 live-service artifact lane 走真实的 Mint checkpoint URI 解析、persistent-cache materialization 和 archive stream，而不是继续 monkeypatch 顶层 artifact backend。
3. 通过测试夹具 source-load `src/openpi` 的 artifact resolver 语义，避免 Mint 自己复制 checkpoint layout 规则。
4. 断言返回的 tar.gz 包含真实 local checkpoint layout，而不是只检查 gzip 头。

**Gate**

- 存在一条 deterministic、service-hosted 的 local checkpoint-layout artifact round-trip lane。
- 这条 lane 不依赖外网、真实 checkpoint 下载或 GPU。

## Phase 3: Freeze The Real-Asset Exploratory Lane

**Modify**

- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-validation-baseline.md`

**Steps**

1. 把 `pi0_aloha_sim` real checkpoint/manual lane 明确写成 exploratory surface，而不是 missing-but-undefined。
2. 记录命令、环境依赖和失败归因口径。
3. 不把 real-asset lane 塞进 must-pass gate。

**Gate**

- real-asset lane 有明确入口，但失败不会被误判成 deterministic contract failure。

## Phase 4: Add Repo/Version Release Discipline

**Modify**

- `src/mint/.github/workflows/test.yml`
- `src/mindlab-toolkit/.github/workflows/test.yml`
- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-validation-baseline.md`

**Steps**

1. 把 Mint、Toolkit 和 cross-repo 组合的 repo/version support status 明确写进 matrix。
2. 先为 Toolkit 落 repo-native workflow，因为它已经可以用 `uv sync` 和 `uv run --with pytest` 在干净环境执行当前 gate。
3. 为 Mint 落 repo-native workflow，因为 `uv sync --frozen --extra dev` 加 documented `uv run pytest ...` gate 在当前仓库已可通过。
4. 记录 capability/version 变更时必须先更新哪些文档，再更新哪些代码。
5. 记录 `src/openpi`、`src/mint`、`src/mindlab-toolkit` 当前 workflow 事实差异，不默认三仓同日发布。

**Gate**

- Toolkit 和 Mint workflow 已落地，后续 contract 变化时不再需要口头约定 repo/version 组合。

## Phase 5: Keep Capability Negotiation Parked Until The Service Contract Exists

**Modify**

- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-validation-baseline.md`

**Steps**

1. 明确 request-side capability header 只是 Toolkit transport identity。
2. 明确 response-side negotiated signal 还不存在。
3. 把 skew detection 继续写成 blocked-by-contract-expansion，而不是假装已经有实现基础。

## Exit Criteria

- localhost real-HTTP smoke 已落地。
- service-hosted local checkpoint-layout artifact round-trip 已落地。
- real-asset lane 和 deterministic gate 被明确区分。
- repo/version release discipline 已写入 progress docs。
- Toolkit 和 Mint repo-native workflow 已落地。
- capability negotiation 的缺失前提被显式记录，而不是被遗漏。

## Not In This Plan

- 真实生产部署 smoke
- 双边 capability/version 协商实现
- RL 或性能压测矩阵
