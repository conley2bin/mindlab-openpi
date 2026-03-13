# OpenPI SFT Contract Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an isolated Mint-native OpenPI SFT training contract without changing the existing low-level `/api/v1/openpi/training/start` bridge.

**Architecture:** Keep the current generic OpenPI training bridge intact. Add a new OpenPI-only SFT request/route/backend path that loads an existing OpenPI config family entry, applies a small whitelist of top-level `TrainConfig` overrides, queues work through the same FutureStore, and exposes matching SDK types and client methods.

**Tech Stack:** FastAPI, Pydantic, dataclasses, httpx, pytest

---

### Task 1: Lock target/docs split before code

**Files:**
- Modify: `docs/targets/target.md`
- Create: `docs/targets/subtarget-09-mint-native-openpi-sft-contract.md`
- Create: `docs/targets/subtarget-10-mint-native-openpi-rl-contract.md`
- Create: `docs/plans/2026-03-13-openpi-training-surfaces-design.md`

**Step 1: Write the docs**

- Record that remote deployment smoke remains `ST-08`
- Record that SFT moves to `ST-09`
- Record that RL stays research-only in `ST-10`

**Step 2: Verify target structure**

Run: `rg -n "^## 子目标总表|^\\| ST-|^## Current Status|^- Status:" docs/targets/target.md docs/targets/subtarget-*.md`
Expected: `ST-09` and `ST-10` appear in both the table and subtarget files with matching status values.

### Task 2: Add failing Mint contract tests for SFT

**Files:**
- Create: `src/mint/tests/test_openpi_sft_training_contract.py`
- Modify: `src/mint/tests/test_openpi_app_registration.py`

**Step 1: Write failing tests**

- backend maps SFT request into OpenPI config overrides and returns `mint://openpi/sft/...`
- route queues `openpi.training.sft.start`
- app registration includes `/api/v1/openpi/training/sft/start`
- unsupported overrides fail with 422 / `OpenPIServiceError`

**Step 2: Run tests to verify failure**

Run: `cd src/mint && python3 -m pytest tests/test_openpi_sft_training_contract.py tests/test_openpi_app_registration.py -q`
Expected: fail because the SFT models/routes/backend do not exist yet.

### Task 3: Add failing Toolkit and cross-repo tests for SFT

**Files:**
- Modify: `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`
- Modify: `src/mint/tests/test_openpi_cross_repo_closed_loop.py`
- Modify: `src/mint/tests/test_openpi_live_service_smoke.py`

**Step 1: Write failing tests**

- SDK posts the nested SFT payload to `/api/v1/openpi/training/sft/start`
- `retrieve_future()` decodes `openpi_sft_training_result`
- fake-runtime closed loop covers SFT future success
- localhost live HTTP smoke covers the new route

**Step 2: Run tests to verify failure**

Run: `python3 -m pytest src/mindlab-toolkit/tests/test_openpi_sdk_contract.py src/mint/tests/test_openpi_cross_repo_closed_loop.py src/mint/tests/test_openpi_live_service_smoke.py -q`
Expected: fail because SDK types/client and Mint route are still missing.

### Task 4: Implement minimal Mint SFT service path

**Files:**
- Modify: `src/mint/tinker_server/openpi/models.py`
- Modify: `src/mint/tinker_server/openpi/routes.py`
- Modify: `src/mint/tinker_server/openpi/backend.py`

**Step 1: Add SFT request/result models**

- isolated request models for config whitelist overrides
- distinct start/result types for the SFT lane

**Step 2: Add backend override builder**

- load template config from OpenPI
- apply supported top-level overrides only
- fail fast on unsupported override fields

**Step 3: Add route**

- queue async background work through existing `future_store`
- keep low-level generic training route unchanged

**Step 4: Run Mint tests**

Run: `cd src/mint && python3 -m pytest tests/test_openpi_sft_training_contract.py tests/test_openpi_app_registration.py -q`
Expected: pass

### Task 5: Implement Toolkit SFT surface

**Files:**
- Modify: `src/mindlab-toolkit/src/mint/openpi/types.py`
- Modify: `src/mindlab-toolkit/src/mint/openpi/client.py`
- Modify: `src/mindlab-toolkit/src/mint/openpi/__init__.py`

**Step 1: Add SFT dataclasses and exports**

- request, start response, result types
- future payload decode for `openpi_sft_training_result`

**Step 2: Add client method**

- `start_sft_training()`

**Step 3: Run SDK tests**

Run: `python3 -m pytest src/mindlab-toolkit/tests/test_openpi_sdk_contract.py -q`
Expected: pass

### Task 6: Re-run shared validation and refresh progress docs

**Files:**
- Modify: `docs/progress/openpi-integration-baseline.md`
- Modify: `docs/progress/openpi-compatibility-matrix.md`
- Modify: `docs/progress/openpi-validation-baseline.md`

**Step 1: Update current truth**

- generic training bridge still exists
- isolated SFT route exists
- RL remains research-only

**Step 2: Run shared tests**

Run: `python3 -m pytest src/mint/tests/test_openpi_sft_training_contract.py src/mint/tests/test_openpi_training_contract.py src/mint/tests/test_openpi_cross_repo_closed_loop.py src/mint/tests/test_openpi_live_service_smoke.py src/mindlab-toolkit/tests/test_openpi_sdk_contract.py -q`
Expected: pass

**Step 3: Structural checks**

Run: `rg -n "^## 子目标总表|^\\| ST-|^## Current Status|^- Status:" docs/targets/target.md docs/targets/subtarget-*.md`
Expected: no missing rows or mismatched status fields

**Step 4: Diff checks**

Run: `git diff --check`
Expected: no whitespace or merge-marker errors

### Task 7: Commit

**Step 1: Review diff**

Run: `git status --short`

**Step 2: Commit**

Run: `git add docs/targets/target.md docs/targets/subtarget-09-mint-native-openpi-sft-contract.md docs/targets/subtarget-10-mint-native-openpi-rl-contract.md docs/plans/2026-03-13-openpi-training-surfaces-design.md docs/plans/2026-03-13-openpi-sft-contract.md docs/progress/openpi-integration-baseline.md docs/progress/openpi-compatibility-matrix.md docs/progress/openpi-validation-baseline.md src/mint/tinker_server/openpi/models.py src/mint/tinker_server/openpi/routes.py src/mint/tinker_server/openpi/backend.py src/mint/tests/test_openpi_sft_training_contract.py src/mint/tests/test_openpi_app_registration.py src/mint/tests/test_openpi_cross_repo_closed_loop.py src/mint/tests/test_openpi_live_service_smoke.py src/mindlab-toolkit/src/mint/openpi/types.py src/mindlab-toolkit/src/mint/openpi/client.py src/mindlab-toolkit/src/mint/openpi/__init__.py src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`

Run: `git commit -m "feat: add isolated openpi sft contract"`
