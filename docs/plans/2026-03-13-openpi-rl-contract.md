# OpenPI RL Contract Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Mint-native OpenPI RL contract only after `src/openpi` owns a real RL runtime facade.

**Architecture:** Keep `ST-10` upstream-first. `src/openpi` must expose an RL-facing integration surface with explicit reward/rollout/update semantics before Mint adds `/api/v1/openpi/training/rl/start` and before Toolkit adds `mint.openpi` RL client types. Do not reuse Mint's existing verl/Megatron RL terminology as the OpenPI public contract unless `src/openpi` adopts the same semantics explicitly.

**Tech Stack:** FastAPI, Pydantic, dataclasses, httpx, pytest, `src/openpi` integration facade, Mint FutureStore

---

### Task 1: Lock the upstream owner surface in `src/openpi`

**Files:**
- Modify: `src/openpi/src/openpi/integration/training.py`
- Create: `src/openpi/src/openpi/integration/rl.py`
- Create: `src/openpi/src/openpi/integration/rl_test.py`
- Modify: `src/openpi/src/openpi/__init__.py`

**Step 1: Write the failing test**

- Add tests that prove `src/openpi` owns:
  - an RL run request object or equivalent dataclass
  - a stable entrypoint for RL execution
  - a result object containing at least run dir, checkpoint dir, and backend/runtime identity
  - explicit failure on unsupported RL backend/runtime combinations

**Step 2: Run test to verify it fails**

Run: `cd src/openpi && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest src/openpi/integration/rl_test.py -q`

Expected: fail because no RL integration facade exists yet.

**Step 3: Write minimal implementation**

- Create a dedicated RL integration module.
- Export it from `src/openpi/src/openpi/__init__.py`.
- Keep supervised `run_training(...)` semantics unchanged.

**Step 4: Run tests to verify they pass**

Run: `cd src/openpi && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest src/openpi/integration/rl_test.py -q`

Expected: pass.

**Step 5: Commit**

```bash
cd src/openpi
git add src/openpi/integration/rl.py src/openpi/integration/rl_test.py src/openpi/integration/training.py src/openpi/__init__.py
git commit -m "feat: add openpi rl integration facade"
```

### Task 2: Freeze RL semantic inputs in `src/openpi`

**Files:**
- Modify: `src/openpi/src/openpi/training/config.py`
- Modify: `src/openpi/src/openpi/training/data_loader.py`
- Create: `src/openpi/src/openpi/training/rl_contract_test.py`

**Step 1: Write the failing test**

- Add tests for the exact RL semantic boundary:
  - rollout input shape
  - reward or advantage carrier shape
  - policy update contract
  - checkpoint resume contract for RL runs
- Add a negative test proving RLDS dataset configuration alone does not count as RL runtime support.

**Step 2: Run test to verify it fails**

Run: `cd src/openpi && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest src/openpi/training/rl_contract_test.py -q`

Expected: fail because current config/data loader surface does not define RL runtime semantics.

**Step 3: Write minimal implementation**

- Add only the RL-specific dataclasses or validation needed by the new integration facade.
- Do not overload existing supervised-only `TrainConfig` if that would merge incompatible semantics.

**Step 4: Run tests to verify they pass**

Run: `cd src/openpi && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest src/openpi/training/rl_contract_test.py -q`

Expected: pass.

**Step 5: Commit**

```bash
cd src/openpi
git add src/openpi/training/config.py src/openpi/training/data_loader.py src/openpi/training/rl_contract_test.py
git commit -m "feat: define openpi rl contract semantics"
```

### Task 3: Add isolated Mint OpenPI RL route only after Tasks 1-2

**Files:**
- Modify: `src/mint/tinker_server/openpi/models.py`
- Modify: `src/mint/tinker_server/openpi/routes.py`
- Modify: `src/mint/tinker_server/openpi/backend.py`
- Create: `src/mint/tests/test_openpi_rl_training_contract.py`

**Step 1: Write the failing test**

- Add tests for:
  - `POST /api/v1/openpi/training/rl/start`
  - explicit request/result types distinct from generic training and SFT
  - queued FutureStore metadata distinct from SFT
  - fail-fast rejection of unsupported top-level fields and unsupported RL backend/runtime combinations

**Step 2: Run test to verify it fails**

Run: `cd src/mint && uv run pytest tests/test_openpi_rl_training_contract.py -q`

Expected: fail because no isolated RL route exists yet.

**Step 3: Write minimal implementation**

- Route must live under OpenPI namespace only.
- Keep `/api/v1/openpi/training/start` and `/api/v1/openpi/training/sft/start` unchanged.
- Backend must delegate into the upstream OpenPI RL facade from Task 1.

**Step 4: Run tests to verify they pass**

Run: `cd src/mint && uv run pytest tests/test_openpi_rl_training_contract.py -q`

Expected: pass.

**Step 5: Commit**

```bash
cd src/mint
git add tinker_server/openpi/models.py tinker_server/openpi/routes.py tinker_server/openpi/backend.py tests/test_openpi_rl_training_contract.py
git commit -m "feat: add isolated openpi rl route"
```

### Task 4: Add Toolkit RL SDK surface only after Task 3

**Files:**
- Modify: `src/mindlab-toolkit/src/mint/openpi/types.py`
- Modify: `src/mindlab-toolkit/src/mint/openpi/client.py`
- Modify: `src/mindlab-toolkit/src/mint/openpi/__init__.py`
- Create: `src/mindlab-toolkit/tests/test_openpi_rl_sdk_contract.py`

**Step 1: Write the failing test**

- Add tests for:
  - RL request serialization
  - RL start response decode
  - RL future payload decode
  - fail-fast on unknown `openpi_*` RL payload types

**Step 2: Run test to verify it fails**

Run: `cd src/mindlab-toolkit && uv run pytest tests/test_openpi_rl_sdk_contract.py -q`

Expected: fail because no RL SDK surface exists yet.

**Step 3: Write minimal implementation**

- Add isolated RL request/result dataclasses and `start_rl_training()` client method.
- Preserve current generic training and SFT behavior.

**Step 4: Run tests to verify they pass**

Run: `cd src/mindlab-toolkit && uv run pytest tests/test_openpi_rl_sdk_contract.py -q`

Expected: pass.

**Step 5: Commit**

```bash
cd src/mindlab-toolkit
git add src/mint/openpi/types.py src/mint/openpi/client.py src/mint/openpi/__init__.py tests/test_openpi_rl_sdk_contract.py
git commit -m "feat: add openpi rl sdk support"
```

### Task 5: Add cross-repo RL validation only after Tasks 1-4

**Files:**
- Modify: `src/mint/tests/test_openpi_cross_repo_closed_loop.py`
- Modify: `src/mint/tests/test_openpi_live_service_smoke.py`
- Modify: `docs/progress/openpi-integration-baseline.md`
- Modify: `docs/progress/openpi-compatibility-matrix.md`
- Modify: `docs/progress/openpi-validation-baseline.md`
- Modify: `docs/targets/subtarget-10-mint-native-openpi-rl-contract.md`

**Step 1: Write the failing test**

- Extend fake-runtime closed loop and localhost live-service smoke to cover RL start and RL future resolution.

**Step 2: Run tests to verify they fail**

Run: `cd src/mint && uv run pytest tests/test_openpi_cross_repo_closed_loop.py tests/test_openpi_live_service_smoke.py -q`

Expected: fail because RL route and SDK surface do not exist yet.

**Step 3: Write minimal implementation**

- Wire the new RL path through existing Mint OpenPI service plane and Toolkit client.
- Update docs only after tests prove the new behavior.

**Step 4: Run verification**

Run:

```bash
cd src/openpi && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest src/openpi/integration/rl_test.py src/openpi/training/rl_contract_test.py -q
cd src/mint && uv run pytest tests/test_openpi_rl_training_contract.py tests/test_openpi_cross_repo_closed_loop.py tests/test_openpi_live_service_smoke.py -q
cd src/mindlab-toolkit && uv run pytest tests/test_openpi_rl_sdk_contract.py -q
cd /home/conley/Documents/mindlab-openpi && git diff --check
```

Expected: all pass.

**Step 5: Commit**

```bash
cd /home/conley/Documents/mindlab-openpi
git add docs/progress/openpi-integration-baseline.md docs/progress/openpi-compatibility-matrix.md docs/progress/openpi-validation-baseline.md docs/targets/subtarget-10-mint-native-openpi-rl-contract.md src/openpi src/mint src/mindlab-toolkit
git commit -m "feat: add openpi rl contract"
```

### Task 6: Do not execute Tasks 3-5 until upstream owner exists

**Files:**
- No code changes

**Step 1: Verify gating**

Run: `rg -n "run_training\\(|run_jax_training\\(|run_pytorch_training\\(" src/openpi/src/openpi/integration/training.py`

Expected: only supervised training entrypoints are present today.

**Step 2: Verify ST-10 stays research-only until Tasks 1-2 land**

Run: `rg -n "^## Current Status|^- Status:" docs/targets/subtarget-10-mint-native-openpi-rl-contract.md`

Expected: `Status: research`
