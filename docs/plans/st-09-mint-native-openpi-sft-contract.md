# ST-09 Mint-Native OpenPI SFT Contract Plan

## Current State

- Status: completed
- Role: canonical plan for the current Mint-native OpenPI SFT surface and its maintenance boundary

## Goal

把 Mint 侧 OpenPI supervised fine-tuning 从“只能启动一个 OpenPI training config”推进到“有独立 SFT 接口、独立 SDK 类型、独立结果语义”的状态，同时不污染其他 Mint 模型族，也不把 Mint 变成 OpenPI 内部训练 DSL 的 owner。

## Boundary Inputs

- `docs/targets/subtarget-09-mint-native-openpi-sft-contract.md`
- `docs/progress/openpi-integration-baseline.md`
- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-contract-glossary.md`
- `src/mint/tinker_server/openpi/{routes,models,backend}.py`
- `src/mint/tinker_server/checkpoints.py`
- `src/mindlab-toolkit/src/mint/openpi/{types,client}.py`
- `src/openpi/src/openpi/training/config.py`

## Canonical Contract Surface

### Service route

- Keep: `POST /api/v1/openpi/training/start`
- Primary SFT entry: `POST /api/v1/openpi/training/sft/start`

### SDK surface

- Keep: `mint.openpi.OpenPIClient.start_training()` as the low-level generic bridge
- Primary SFT entry: `mint.openpi.OpenPIClient.start_sft_training()`

### Request shape

SFT request stays on a small, explicit surface:

- `config_name`
- `exp_name`
- `backend`
- `overwrite`
- `resume`
- `config_overrides`
  - `batch_size`
  - `num_train_steps`
  - `log_interval`
  - `save_interval`
  - `keep_period`
  - `wandb_enabled`
  - `seed`

### Validation rules

- Top-level unknown request fields fail fast with `422`
- Unknown or unsupported `config_overrides` fields fail fast with `422`
- Mint only applies top-level `TrainConfig` overrides that already exist upstream in `src/openpi`
- Mint does not accept HTTP-side authoring of `model`, `data`, `weight_loader`, `optimizer`, `lr_schedule` or similar nested OpenPI internals

### Result semantics

- SFT future payload remains separate from generic training payload
- Mint-exposed SFT checkpoint alias stays `mint://openpi/sft/<config>/<exp>/<step>`
- Mint checkpoint resolution must normalize that alias back to the real OpenPI checkpoint tree before artifact/archive/resume paths are used

## Non-Goals

- Do not delete or repurpose the generic training bridge
- Do not merge SFT and future RL semantics into one endpoint
- Do not expose the full OpenPI `TrainConfig` authoring surface over HTTP
- Do not change Mint non-OpenPI model families
- Do not move remote deployment smoke or real-checkpoint ownership into `ST-09`

## Maintenance Checklist

When this slice changes, re-check at least these surfaces:

- `src/mint/tests/test_openpi_sft_training_contract.py`
- `src/mint/tests/test_openpi_training_contract.py`
- `src/mint/tests/test_openpi_cross_repo_closed_loop.py`
- `src/mint/tests/test_openpi_live_service_smoke.py`
- `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`

## Follow-Up Boundary

Any request to expose deeper SFT authoring knobs should be blocked until `src/openpi` first stabilizes those knobs as an upstream integration-facing surface. `ST-09` owns the Mint-side contract split, not the upstream training runtime truth.
