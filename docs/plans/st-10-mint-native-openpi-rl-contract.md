# ST-10 Mint-Native OpenPI RL Contract Plan

## Current State

- Status: research
- Role: canonical plan for the RL boundary and promotion gate; not an approved implementation order for Mint routes yet

## Goal

在不污染现有 Mint 模型族、也不伪造 OpenPI runtime owner 的前提下，提前固定未来 OpenPI RL 接口的边界、前置条件和禁止动作。

## Boundary Inputs

- `docs/targets/subtarget-10-mint-native-openpi-rl-contract.md`
- `docs/progress/openpi-integration-baseline.md`
- `docs/progress/openpi-contract-glossary.md`
- `src/openpi/src/openpi/integration/training.py`
- `src/openpi/src/openpi/training/config.py`
- `src/mint/tinker_server/routes/training.py`
- `src/mint/tinker_server/backend/{megatron_training.py,verl_patches.py}`

## Current Constraint

`src/openpi` 现在只有 supervised training facade。它还没有一个稳定的 RL runtime facade 去表达 rollout input、reward or advantage carrier、policy update step、resume contract 和 backend/runtime identity。只要这层 upstream owner 不存在，Mint 和 Toolkit 都不能先发布 RL API。

## Rejected Direction

不要先在 Mint 侧做一个“看起来像 RL”的 HTTP 接口，再等 `src/openpi` 以后补齐语义。那样会反过来让 Mint 猜 upstream 语义，形成假 owner。尤其不能把现有 Mint verl 或 Megatron 训练术语直接包装成 OpenPI public contract。

## What Must Exist Upstream First

Before Mint adds any OpenPI RL route, `src/openpi` must own all of these:

- a stable RL-facing request object or equivalent integration dataclass
- a stable RL execution entrypoint
- a typed result object with at least run location, checkpoint location, and backend/runtime identity
- explicit validation for unsupported RL backend/runtime combinations
- explicit resume semantics for RL runs
- semantic ownership of rollout/reward/update vocabulary

## What Is Forbidden Before That Gate

- no `POST /api/v1/openpi/training/rl/start`
- no `mint.openpi` RL SDK method
- no reuse of Mint’s existing verl or Megatron RL terms as if they were already OpenPI public semantics
- no “temporary” RL HTTP schema that guesses upstream meanings

## Promotion Path After The Gate Opens

Promotion order stays fixed:

1. `src/openpi` exposes the RL runtime facade and tests it
2. Mint adds an isolated OpenPI RL route under `/api/v1/openpi/...`
3. Toolkit adds isolated RL request/result types and client methods
4. Cross-repo validation covers fake-runtime and local live-service lanes
5. Only then can `ST-10` leave `research`

## Non-Goals

- Do not overload the current generic training bridge with RL-specific fields
- Do not merge RL and SFT into one “training” contract
- Do not treat RLDS dataset config as proof that an RL runtime surface already exists
- Do not let this slice block `ST-08` remote deployment work or `ST-09` SFT maintenance

## Review Trigger

If `src/openpi` later lands a real RL integration module or equivalent public facade, this file becomes the first place to rewrite. Until then, this plan is a guardrail, not an implementation ticket.
