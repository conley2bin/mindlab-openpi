# ST-05 Cross-Repo Validation And Compatibility Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立一套持续有效的跨仓验证机制，既能证明 OpenPI 新路径可用，也能证明现有 Mint/Tinker-compatible 路径没有被污染。

**Architecture:** `ST-05` 不是最后补的测试清单，而是从第一天就生效的 deterministic gating policy。先写 compatibility matrix 和 repo-local gate 分类，再让 `ST-02`、`ST-03`、`ST-04` 各自补本地 contract tests，最后组装 fake-runtime closed loop。localhost real-HTTP smoke、real checkpoint/manual lane 和 repo/version release discipline 转入 `ST-06`，不再塞进 `ST-05` 已完成范围。

**Tech Stack:** Markdown, pytest, `uv`, repo-local test suites, CI workflows

---

## Boundary Inputs

- `docs/progress/openpi-integration-baseline.md`
- `docs/progress/openpi-contract-glossary.md`

This plan inherits these `ST-01` rules:

- `src/openpi` owns semantic objects, `src/mint` owns service envelopes, `src/mindlab-toolkit` owns SDK naming and transport identity.
- Cross-repo validation must verify both positive OpenPI behavior and negative non-pollution of existing Mint/Tinker-compatible paths.
- Failure attribution must classify drift at the runtime, service, SDK or environment layer instead of collapsing everything into one “integration failed” bucket.

## Deliverables

- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-validation-baseline.md`
- Repo-local contract tests added by `ST-02`, `ST-03`, `ST-04`
- Cross-repo minimal closed-loop tests after repo-local gates stabilize

## Existing Validation Reality

- `src/openpi/.github/workflows/test.yml` 当前会跑 `uv run pytest --strict-markers -m "not manual"`。
- `src/openpi/src/openpi/models/model_test.py` 同时包含 deterministic local tests 和 `test_model_restore` manual case；任何硬门禁命令都必须显式过滤 manual marker 或 node id。
- `src/openpi/src/openpi/policies/policy_test.py` 是 `manual`，不能当 CI gate。
- `src/openpi/src/openpi/shared/download_test.py` 依赖远端资源，适合 exploratory lane，不适合首批硬门禁。
- `src/mint` 已经有大量旧路径 regression anchors，特别是 config、gateway、user-agent、prompt-logprobs 语义。
- `src/mindlab-toolkit` 目前只有两组硬约束测试: namespace contract 和 patch behavior。
- workspace root 当前没有 `tests/`、`scripts/`、`.github/`，因此 root-level harness/CI 不是既有执行面，而是额外 integration-infra 决策。

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
cd src/openpi && uv run pytest --strict-markers -m "not manual" src/openpi/models/model_test.py -q
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
  tests/test_issue_281_scheduler_and_healthz.py \
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
2. `test_model_restore`、manual policy inference、远端 download tests 全部明确归到 exploratory lane；不能混进 deterministic gate。
3. 不允许把远端 checkpoint、manual policy inference、跨仓联调当成 repo-local 替代品。
4. 每个 ST 的 exit gate 都必须先通过对应 repo-local lane。

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

- Update `docs/progress/openpi-validation-baseline.md`

**Steps**

1. 第一条跨仓闭环必须使用 fake runtime or test double，不直接依赖真实 released checkpoint。
2. 在实现前先做 harness ownership 决策，只允许三种落点：
   - workspace root
   - `src/mint/tests/` 作为 service-hosted integration lane
   - 单独 integration repo
3. 在 ownership 未决前，`ST-05` 先只冻结闭环验证 contract 和通过条件，不预先承诺文件落点。
4. 最小闭环顺序固定为:
   - `src/openpi` runtime facade returns deterministic fake observation/action result
   - `src/mint` service plane wraps and returns it
   - `src/mindlab-toolkit` SDK calls service and decodes response
5. 闭环必须验证结构化 observation/action payload，不只看 200 OK。
6. 闭环必须包含至少一个 lifecycle signal，例如 `reset()` 或 action chunk boundary。
7. 闭环失败时必须在 baseline 文档里归因到具体层级。

**Gate**

- 跨仓最小闭环可在本地跑通，不依赖外网和大模型 checkpoint。

## Phase 5: Handoff Operational Validation And Release Discipline To ST-06

`ST-05` 的完成边界停在 deterministic repo-local gates 和 fake-runtime closed loop。下面这些工作显式移交给 `ST-06`：

- localhost real-HTTP live-service smoke
- real checkpoint/manual lane
- Mint、Toolkit 与 cross-repo repo/version release discipline
- capability/version skew detection 的前置条件梳理

## Exit Criteria

- compatibility matrix 和 validation baseline 存在并持续维护。
- 三仓各自有 must-pass local contract tests。
- 存在一条 deterministic、无外网依赖的 cross-repo minimal closed loop。
- localhost real-HTTP smoke、真实 checkpoint/manual lane 与 release discipline 不再作为 `ST-05` 未完成事项残留，而是进入 `ST-06`。

## Not In This Plan

- 具体 runtime/service/sdk feature implementation
- 大规模性能压测
- RL 全量验证矩阵
- localhost real-HTTP smoke、real-asset/manual lane、repo/version release discipline
