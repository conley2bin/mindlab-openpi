# OpenPI Validation Baseline

Baseline date: 2026-03-11

## Current Hard Gates

### `src/openpi`

```bash
cd src/openpi && uv run pytest src/openpi/models/model_test.py -q
cd src/openpi && uv run pytest src/openpi/models/lora_test.py -q
cd src/openpi && uv run pytest scripts/train_test.py -q
```

What these gates cover:

- local model creation and loss/sample behavior
- local LoRA model surface
- local JAX training smoke with `debug` config and resume path

What these gates do not cover:

- Mint-facing integration facade
- real checkpoint inference
- cross-repo contract

### `src/mint`

```bash
cd src/mint && pytest \
  tests/test_issue_136_config_file_validation.py \
  tests/test_model_registry_env_config.py \
  tests/test_gateway_multi_target_routing.py \
  tests/test_client_compat_user_agent.py \
  tests/test_tinker_prompt_logprobs_semantics.py -q
```

What these gates cover:

- config file validation
- model registry env overrides
- gateway multi-target routing behavior
- client user-agent compatibility logic
- prompt logprobs semantics for the Tinker-compatible path

What these gates do not cover:

- any OpenPI route
- any OpenPI schema
- any OpenPI runtime bridge

### `src/mindlab-toolkit`

```bash
cd src/mindlab-toolkit && pytest \
  tests/test_namespace_contract.py \
  tests/test_mint_polling_patch.py -q
```

What these gates cover:

- current top-level namespace contract
- current patch side effects for the Tinker-compatible layer

What these gates do not cover:

- `mint.openpi.*`
- OpenPI service client transport
- SDK mapping to Mint OpenPI service schemas

## Current Weak Lanes

These are useful, but they are not hard gates for the first implementation pass.

| Repo | Weak lane | Why weak |
| --- | --- | --- |
| `src/openpi` | `src/openpi/src/openpi/policies/policy_test.py` | marked `manual`; depends on real checkpoint download and actual inference |
| `src/openpi` | `src/openpi/src/openpi/shared/download_test.py` | depends on remote assets |
| cross-repo | any future real checkpoint closed loop | not deterministic; mixes contract problems with resource/network problems |

## Missing Validation Layers

| Layer | Current state |
| --- | --- |
| OpenPI integration facade tests | missing |
| Mint OpenPI route and schema tests | missing |
| Mint to OpenPI runtime bridge tests | missing |
| Toolkit `mint.openpi.*` namespace tests | missing |
| Toolkit OpenPI SDK contract tests | missing |
| deterministic cross-repo closed loop | missing |
| release matrix by repo/version combination | missing |

## Positive And Negative Signals To Preserve

| Area | Positive signal | Negative signal |
| --- | --- | --- |
| OpenPI | local runtime/training tests still pass after facade extraction | script adapters stop working or local training smoke breaks |
| Mint | new OpenPI plane works without touching token-only types | old `/api/v1` path changes semantics or old tests need relaxed assertions |
| Toolkit | `mint.openpi.*` imports and behaves as designed | top-level `mint.*` re-export or existing patch behavior changes |
| Cross-repo | deterministic fake-runtime loop works end-to-end | failure cannot be localized to runtime vs service vs SDK |

## Failure Attribution Rule

When a future cross-repo test fails, the write-up must classify it into one of these buckets first:

- `src/openpi` runtime surface failure
- `src/mint` service/schema/bridge failure
- `src/mindlab-toolkit` SDK/namespace failure
- environment or external asset failure

Do not write “OpenPI integration failed” without this classification.

## First Deterministic Closed-Loop Rule

The first cross-repo closed loop must satisfy all of these constraints:

- no external checkpoint download
- no `manual` marker
- no websocket server dependency
- fake runtime or test double allowed
- verifies structured observation/action payload
- verifies at least one lifecycle signal such as `reset()` or action chunk boundary
