# ST-05 Cross-Repo Validation And Compatibility Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立一套持续有效的跨仓验证机制，既能证明 OpenPI 新路径可用，也能证明现有 Mint/Tinker-compatible 路径没有被污染。

**Architecture:** `ST-05` 不是最后补的测试清单，而是从第一天就生效的 gating policy。先写 compatibility matrix 和 repo-local gate 分类，再让 `ST-02`、`ST-03`、`ST-04` 各自补本地 contract tests，最后才组装跨仓最小闭环。真实 checkpoint 和 manual lane 只能作为后置验证，不应充当唯一证明。

**Tech Stack:** Markdown, pytest, `uv`, repo-local test suites, CI workflows

---

## Deliverables

- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-validation-baseline.md`
- Repo-local contract tests added by `ST-02`, `ST-03`, `ST-04`
- Cross-repo minimal closed-loop tests after repo-local gates stabilize

## Existing Validation Reality

- `src/openpi/.github/workflows/test.yml` 当前会跑 `uv run pytest --strict-markers -m "not manual"`。
- `src/openpi/src/openpi/policies/policy_test.py` 是 `manual`，不能当 CI gate。
- `src/openpi/src/openpi/shared/download_test.py` 依赖远端资源，适合 exploratory lane，不适合首批硬门禁。
- `src/mint` 已经有大量旧路径 regression anchors，特别是 config、gateway、user-agent、prompt-logprobs 语义。
- `src/mindlab-toolkit` 目前只有两组硬约束测试: namespace contract 和 patch behavior。

## Phase 1: Write The Compatibility Matrix Before Feature Work

**Create**

- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-validation-baseline.md`

**Steps**

1. 记录首批承诺支持的模型/模式集合，不再写模糊的 “pi0 family”。
2. 为三仓分别写出 canonical responsibility 和 validation owner。
3. 把每一条验证项拆成 positive signal 和 negative signal。
4. 基线文档只写 current support status，不写未来愿景。

**Minimum Matrix Columns**

- layer
- owner repo
- supported capability
- must-pass local tests
- exploratory tests
- negative regression anchors
- notes

**Gate**

- 在任何 OpenPI feature merge 前，matrix 已存在并可更新。

## Phase 2: Classify Repo-Local Gates Explicitly

**OpenPI local gates**

```bash
cd src/openpi && uv run pytest src/openpi/models/model_test.py -q
cd src/openpi && uv run pytest src/openpi/models/lora_test.py -q
cd src/openpi && uv run pytest scripts/train_test.py -q
```

**Mint local gates**

```bash
cd src/mint && pytest \
  tests/test_issue_136_config_file_validation.py \
  tests/test_model_registry_env_config.py \
  tests/test_gateway_multi_target_routing.py \
  tests/test_client_compat_user_agent.py \
  tests/test_tinker_prompt_logprobs_semantics.py -q
```

**Toolkit local gates**

```bash
cd src/mindlab-toolkit && pytest \
  tests/test_namespace_contract.py \
  tests/test_mint_polling_patch.py -q
```

**Steps**

1. 把 must-pass local gates 和 exploratory/manual lanes 分开写。
2. 不允许把远端 checkpoint、manual policy inference、跨仓联调当成 repo-local 替代品。
3. 每个 ST 的 exit gate 都必须先通过对应 repo-local lane。

## Phase 3: Land Repo-Local Contract Tests In The Owning ST

**Expected New Anchors**

- `src/openpi/src/openpi/integration/runtime_test.py`
- `src/openpi/src/openpi/integration/artifacts_test.py`
- `src/openpi/src/openpi/integration/training_test.py`
- `src/mint/tests/test_openpi_app_registration.py`
- `src/mint/tests/test_openpi_service_contract.py`
- `src/mint/tests/test_openpi_runtime_bridge.py`
- `src/mint/tests/test_openpi_does_not_pollute_tinker_types.py`
- `src/mindlab-toolkit/tests/test_openpi_namespace_contract.py`
- `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`

**Steps**

1. `ST-02`、`ST-03`、`ST-04` 各自负责新增本仓 contract tests。
2. `ST-05` 只负责统一口径和 gating policy，不替代 owning repo 编写 contract tests。
3. 每个新测试都必须对应到 matrix 中的一条 capability 或 negative regression item。

## Phase 4: Add A Cross-Repo Minimal Closed Loop With A Fake Runtime First

**Create**

- `src/mint/tests/test_openpi_runtime_bridge.py`
- `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`
- Update `docs/progress/openpi-validation-baseline.md`

**Steps**

1. 第一条跨仓闭环必须使用 fake runtime or test double，不直接依赖真实 released checkpoint。
2. 最小闭环顺序固定为:
   - `src/openpi` runtime facade returns deterministic fake observation/action result
   - `src/mint` service plane wraps and returns it
   - `src/mindlab-toolkit` SDK calls service and decodes response
3. 闭环必须验证结构化 observation/action payload，不只看 200 OK。
4. 闭环必须包含至少一个 lifecycle signal，例如 `reset()` 或 action chunk boundary。
5. 闭环失败时必须在 baseline 文档里归因到具体层级。

**Gate**

- 跨仓最小闭环可在本地跑通，不依赖外网和大模型 checkpoint。

## Phase 5: Add Real-Asset And Manual Validation As A Separate Lane

**Exploratory Commands**

```bash
cd src/openpi && uv run pytest --strict-markers -m "manual" src/openpi/policies/policy_test.py
cd src/openpi && uv run pytest src/openpi/shared/download_test.py -q
```

**Steps**

1. 在 repo-local 和 fake-runtime closed-loop 稳定后，再补真实 checkpoint/manual lane。
2. 真实资源验证写入 matrix 和 baseline，但不替代本地 deterministic lane。
3. 如果真实 checkpoint lane 失败，先判定是 network/resource 问题还是 contract drift，不允许直接写成 “OpenPI 集成失败”。

## Phase 6: Wire CI And Release Discipline

**Inspect Or Modify**

- `src/openpi/.github/workflows/test.yml`
- CI definitions for `src/mint`
- CI definitions for `src/mindlab-toolkit`
- `docs/progress/openpi-compatibility-matrix.md`

**Steps**

1. 维持 `openpi` 现有 `not manual` CI lane。
2. 为 Mint 和 Toolkit 增加等价的 hard-gate commands，至少覆盖现有 regression anchors 和新增 OpenPI contract tests。
3. 每次 capability 或 version 组合变化时，先更新 matrix，再更新代码和 release notes。
4. 明确支持的 repo/version 组合；不要默认三仓永远同日发布。

## Exit Criteria

- compatibility matrix 和 validation baseline 存在并持续维护。
- 三仓各自有 must-pass local contract tests。
- 存在一条 deterministic、无外网依赖的 cross-repo minimal closed loop。
- 真实 checkpoint/manual lane 与 deterministic lane 被明确区分。

## Not In This Plan

- 具体 runtime/service/sdk feature implementation
- 大规模性能压测
- RL 全量验证矩阵
