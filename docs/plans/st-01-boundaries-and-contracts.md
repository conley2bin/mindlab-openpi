# ST-01 Integration Boundaries And Contracts Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 OpenPI 接入 Mint 的边界、术语和职责分工冻结成后续实现必须遵守的工程约束。

**Architecture:** `ST-01` 只做 boundary freeze，不做功能实现。交付物是 baseline 文档、glossary 和 downstream plan 对齐，不是 service、runtime 或 SDK 代码。后续 `ST-02` 到 `ST-05` 都只能在这里冻结的 vocabulary 和 ownership 上展开。

**Tech Stack:** Markdown, `rg`, pytest anchors in `src/mint`, `src/openpi`, `src/mindlab-toolkit`

---

## Deliverables

- `docs/progress/openpi-integration-baseline.md`
- `docs/progress/openpi-contract-glossary.md`
- Updated `docs/plans/st-02-openpi-runtime-surface.md`
- Updated `docs/plans/st-03-mint-openpi-service-plane.md`
- Updated `docs/plans/st-04-mindlab-toolkit-openpi-sdk.md`
- Updated `docs/plans/st-05-cross-repo-validation-and-compatibility.md`

## Existing Repo Anchors

- `src/mint/tinker_server/models/types.py` 是当前 Mint canonical token/chunk service schema。
- `src/mint/tinker_server/routes/service.py` 和 `src/mint/tinker_server/routes/sampling.py` 是当前 Tinker-compatible session/sampling 语义入口。
- `src/openpi/src/openpi/policies/policy.py` 和 `src/openpi/packages/openpi-client/src/openpi_client/base_policy.py` 定义当前 `obs -> action` / `reset()` policy contract。
- `src/openpi/src/openpi/policies/policy_config.py` 是当前训练产物到 inference policy 的装配边界。
- `src/mindlab-toolkit/src/mint/__init__.py`、`src/mindlab-toolkit/src/mint/tinker/__init__.py`、`src/mindlab-toolkit/src/mint/mint/__init__.py` 共同定义当前 `mint.*` public namespace 和 patch side effects。
- `src/mindlab-toolkit/tests/test_namespace_contract.py` 是当前 SDK namespace 的硬约束。

## Phase 1: Freeze Current Truth

**Inspect**

- `docs/targets/target.md`
- `docs/targets/subtarget-01-boundaries-and-contracts.md`
- `src/mint/tinker_server/models/types.py`
- `src/mint/tinker_server/routes/service.py`
- `src/mint/tinker_server/routes/sampling.py`
- `src/openpi/src/openpi/policies/policy.py`
- `src/openpi/src/openpi/policies/policy_config.py`
- `src/openpi/packages/openpi-client/src/openpi_client/base_policy.py`
- `src/mindlab-toolkit/src/mint/__init__.py`
- `src/mindlab-toolkit/src/mint/tinker/__init__.py`
- `src/mindlab-toolkit/src/mint/mint/__init__.py`
- `src/mindlab-toolkit/tests/test_namespace_contract.py`

**Write**

- `docs/progress/openpi-integration-baseline.md`

**Steps**

1. 记录 `src/mint` 当前 token-only service truth，不写未来 OpenPI 设计。
2. 记录 `src/openpi` 当前 observation/action/multimodal/reset truth，不把它翻译成 token 语义。
3. 记录 `src/mindlab-toolkit` 当前 namespace truth 和 import side effects。
4. 在 baseline 文档里分开写 “current truth” 和 “gap to target”，不要把未来方案写进 current truth。

**Commands**

```bash
rg -n "class SampleRequest|class CreateSamplingSessionRequest|class SampleResponse" \
  src/mint/tinker_server/models/types.py
rg -n "def infer|def reset|class Policy|create_trained_policy" \
  src/openpi/src/openpi/policies/policy.py \
  src/openpi/src/openpi/policies/policy_config.py \
  src/openpi/packages/openpi-client/src/openpi_client/base_policy.py
rg -n "__all__|apply_mint_patches|ServiceClient|TrainingClient|SamplingClient" \
  src/mindlab-toolkit/src/mint/__init__.py \
  src/mindlab-toolkit/src/mint/tinker/__init__.py \
  src/mindlab-toolkit/src/mint/mint/__init__.py
cd src/mindlab-toolkit && pytest tests/test_namespace_contract.py -q
```

**Gate**

- baseline 文档只描述当前状态和目标差距，没有 implementation steps。
- baseline 文档能直接回答 “今天哪一层负责什么” 和 “今天哪一层还没有”。

## Phase 2: Freeze Vocabulary And Ownership

**Write**

- `docs/progress/openpi-contract-glossary.md`

**Steps**

1. 定义至少这些术语的唯一含义: runtime, policy, service contract, artifact, session, episode, action chunk, checkpoint。
2. 定义 ownership matrix:
   - `src/openpi` 持有 semantic objects 和 runtime truth。
   - `src/mint` 持有 service envelope、task orchestration、ops surface。
   - `src/mindlab-toolkit` 持有 public SDK naming 和 client ergonomics。
3. 明确 forbidden moves:
   - 不把 OpenPI observation/action 伪装成 Mint 现有 token request。
   - 不把 `mint.openpi.*` 偷偷 re-export 到现有顶层 `mint.*`。
   - 不在 Mint 或 Toolkit 内复制 OpenPI 私有 runtime logic。
4. 明确允许跨仓传递的对象边界，禁止 “双方各自定义一份 canonical schema”。

**Commands**

```bash
rg -n "mint\\.tinker|TINKER_COMPAT_EXPORTS|/api/v1|sampling_session_id|model_id" \
  src/mint src/mindlab-toolkit
rg -n "action_chunk|metadata|policy_timing|reset\\(" src/openpi
```

**Gate**

- glossary 文档能直接回答每个术语属于哪一仓的 canonical definition。
- glossary 文档里列出了禁止事项，不只是抽象原则。

## Phase 3: Push The Rules Into Downstream Plans

**Modify**

- `docs/plans/st-02-openpi-runtime-surface.md`
- `docs/plans/st-03-mint-openpi-service-plane.md`
- `docs/plans/st-04-mindlab-toolkit-openpi-sdk.md`
- `docs/plans/st-05-cross-repo-validation-and-compatibility.md`

**Steps**

1. 把 glossary 和 ownership matrix 写成 downstream plan 的前置约束，而不是附录。
2. 删除 downstream plans 里重复定义 vocabulary 的段落，避免 drift。
3. 把 repo-local guardrail tests 留给 owning ST:
   - `ST-02` 持有 OpenPI runtime contract tests。
   - `ST-03` 持有 Mint service pollution guardrails。
   - `ST-04` 持有 Toolkit namespace guardrails。
4. `ST-01` 不承担功能代码或 repo-local feature tests 的实现。

**Gate**

- `ST-02` 到 `ST-05` 不再重复发明 naming rules。
- `ST-01` 结束时没有 OpenPI feature code 进入任何仓库。

## Exit Criteria

- `docs/progress/openpi-integration-baseline.md` 存在且只描述 current truth 和 gap。
- `docs/progress/openpi-contract-glossary.md` 存在且明确 ownership 与 forbidden moves。
- `ST-02` 到 `ST-05` 都显式引用同一套术语和边界。

## Not In This Plan

- `src/openpi` integration facade 实现
- Mint OpenPI route family
- `mint.openpi.*` SDK
- Cross-repo closed-loop tests
