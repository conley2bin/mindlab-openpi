# ST-03 Mint OpenPI Service Plane Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `src/mint` 内建立独立的 OpenPI service plane，让 Mint 能承载 OpenPI inference、artifact 和后续训练能力，同时不污染现有 Tinker-compatible `/api/v1` token-centric contract。

**Architecture:** 第一阶段只引入显式 `openpi` route family、config gate 和 runtime bridge，不碰现有 `tinker_server/models/types.py`。第二阶段再增加只读 artifact endpoint，最后才增加 training endpoint。现有 `gateway.py` 先作为负向回归锚点，不进入首批 OpenPI 方案；远端多目标路由属于后续扩展，不应挤进最小闭环。

**Tech Stack:** FastAPI, Pydantic, `tinker_server/app.py`, `tinker_server/config.py`, `tinker_server/config_file.py`, pytest

---

## Existing Repo Anchors

- `src/mint/tinker_server/app.py` 是当前 router registration 和 lifecycle assembly 入口。
- `src/mint/tinker_server/models/types.py` 明确声明这些类型 “match the tinker client API for compatibility”。
- `src/mint/tinker_server/config.py` 和 `src/mint/tinker_server/config_file.py` 共同定义 env/TOML config surface。
- `src/mint/tinker_server/routes/service.py`、`sampling.py`、`training.py` 是当前 public `/api/v1` family。
- `src/mint/tinker_server/routes/weights.py` 持有 checkpoint archive / upload / proxy 语义。
- `src/mint/tinker_server/backend/future_store.py`、`resource_pool.py`、`session_manager.py`、`training_session_manager.py` 是可复用的 platform primitives。
- `src/mint/tinker_server/gateway.py` 是现有 remote target routing 逻辑，不应默认成为 OpenPI MVP 范围。
- `src/mint/tinker_server/client_compat.py` 持有旧 SDK 的 User-Agent 与 checkpoint URI 兼容逻辑，OpenPI plane 不能无意复用它。

## Must-Pass Existing Regression Anchors

```bash
cd src/mint && pytest \
  tests/test_issue_136_config_file_validation.py \
  tests/test_model_registry_env_config.py \
  tests/test_gateway_multi_target_routing.py \
  tests/test_client_compat_user_agent.py \
  tests/test_issue_281_scheduler_and_healthz.py \
  tests/test_tinker_prompt_logprobs_semantics.py -q
```

后续任何 OpenPI 变更都不能通过修改这些旧测试的断言来“放行”。

## Recommended Package Layout

- `src/mint/tinker_server/openpi/__init__.py`
- `src/mint/tinker_server/openpi/models.py`
- `src/mint/tinker_server/openpi/backend.py`
- `src/mint/tinker_server/openpi/routes.py`

## Phase 1: Reserve The Service Namespace And Config Surface

**Create**

- `src/mint/tinker_server/openpi/__init__.py`
- `src/mint/tests/test_openpi_app_registration.py`
- `src/mint/tests/test_openpi_config_validation.py`

**Modify**

- `src/mint/tinker_server/app.py`
- `src/mint/tinker_server/config.py`
- `src/mint/tinker_server/config_file.py`

**Steps**

1. 为 OpenPI 增加显式 config gate，默认关闭。
2. 在 env config 和 TOML config 两层都定义 OpenPI 配置，不允许只改 `ServerConfig` 而遗漏 `config_file.py`。
3. 预留显式 route family。推荐 public 路径使用 `/api/v1/openpi/*`，internal/ops 路径使用 `/internal/openpi/*`。
4. 新 route family 默认走现有 auth middleware、trace/metering 和 route labeling 逻辑；除非有明确需求，不新增 unauthenticated path 或 OTEL exclusion。
5. route registration 只在 OpenPI enabled 时发生，关闭时不改变现有 app surface。
6. `models/types.py` 在本 phase 保持不动；任何 OpenPI schema 都不能先塞进现有 token-only types tree。

**Commands**

```bash
cd src/mint && pytest \
  tests/test_issue_136_config_file_validation.py \
  tests/test_model_registry_env_config.py \
  tests/test_issue_281_scheduler_and_healthz.py \
  tests/test_openpi_app_registration.py \
  tests/test_openpi_config_validation.py -q
```

**Gate**

- OpenPI disabled 是默认行为。
- 配置错误 fail-fast，不静默回退到现有 LLM 路径。
- `app.py` 注册 OpenPI routes 后，旧 route family 不改义。
- `healthz`、根路径响应与既有认证语义不改义。

## Phase 2: Define An OpenPI-Specific Service Schema Family

**Create**

- `src/mint/tinker_server/openpi/models.py`
- `src/mint/tests/test_openpi_service_contract.py`
- `src/mint/tests/test_openpi_does_not_pollute_tinker_types.py`

**Steps**

1. 在 `openpi/models.py` 中定义 OpenPI request/response models，表达 observation/action/multimodal payload。
2. service envelope 字段归 Mint 所有；semantic payload 字段保持与 `ST-02` runtime surface 对齐。
3. 明确 `reset()` / episode boundary / action chunk lifecycle 不等于现有 sampling session 语义。
4. `tinker_server/models/types.py` 不增加 OpenPI 语义别名。

**Commands**

```bash
cd src/mint && pytest \
  tests/test_tinker_prompt_logprobs_semantics.py \
  tests/test_openpi_service_contract.py \
  tests/test_openpi_does_not_pollute_tinker_types.py -q
```

**Gate**

- OpenPI service schema 独立存在。
- 旧 token/chunk schema 没有新增 OpenPI-specific optional fields。

## Phase 3: Build The Runtime Bridge

**Create**

- `src/mint/tinker_server/openpi/backend.py`
- `src/mint/tests/test_openpi_runtime_bridge.py`

**Modify**

- `src/mint/tinker_server/openpi/routes.py`

**Steps**

1. 由 Mint bridge 调用 `src/openpi` 的 `integration.runtime` facade，不直接 import 研究期内部对象。
2. 定义 Mint service lifecycle 到 OpenPI policy lifecycle 的映射。
3. 明确错误映射，不吞掉 OpenPI runtime errors。
4. 首个闭环只覆盖 inference path。training 和 artifact path 后置到下一 phase。

**Commands**

```bash
cd src/mint && pytest \
  tests/test_openpi_runtime_bridge.py \
  tests/test_openpi_service_contract.py -q
```

**Gate**

- inference-only OpenPI path 可通过 Mint service surface 访问。
- runtime bridge tests 不依赖真实远端 checkpoint；优先使用 fake runtime or test double。

## Phase 4: Add Read-Only Artifact Endpoints After Inference Stabilizes

**Modify**

- `src/mint/tinker_server/openpi/routes.py`
- `src/mint/tinker_server/openpi/backend.py`
- `src/mint/tinker_server/checkpoints.py`
- `src/mint/tests/test_openpi_artifact_proxy.py`

**Steps**

1. 先把 artifact 查询、download proxy 建在 OpenPI route family 下，不在这一 phase 引入 training task orchestration。
2. 只复用 Mint 的 future store、capacity control、ops surface；不要复用 token-centric request types。
3. 如果 OpenPI artifact route 需要复用现有 checkpoint archive/upload machinery，必须显式隔离旧 `client_compat.py` 的 URI/User-Agent 分支，不靠默认行为猜协议。
4. 如果某个现有 backend primitive 与 OpenPI lifecycle 冲突，就单独实现 OpenPI path，不强求复用。
5. `gateway.py` 继续只作为旧路径回归锚点，除非明确需要 remote OpenPI deployment routing。

**Commands**

```bash
cd src/mint && pytest \
  tests/test_issue_190_checkpoint_archive_auth_signed_url.py \
  tests/test_issue_218_gateway_checkpoint_proxy.py \
  tests/test_openpi_artifact_proxy.py -q
```

**Gate**

- inference 稳定前不引入 OpenPI training routes。
- OpenPI artifact semantics 不污染现有 `mint://` / `tinker://` checkpoint contract。

## Phase 5: Add Training Endpoints Only After Artifact Contract Stabilizes

**Modify**

- `src/mint/tinker_server/openpi/routes.py`
- `src/mint/tinker_server/openpi/backend.py`
- `src/mint/tests/test_openpi_training_contract.py`

**Steps**

1. 在 inference route 和只读 artifact route 稳定后，再增加 OpenPI training task orchestration。
2. 训练 route 只消费 `ST-02` training facade，不直接编排 OpenPI 内部训练脚本参数。
3. 训练 endpoint 的 future/polling/object naming 必须延续前面已经冻结的 OpenPI service schema family，不回退到现有 token-centric training types。

**Gate**

- SDK 首个 cut 不依赖这一 phase。
- training route 不会反向重定义 inference 或 artifact contract。

## Phase 6: Lock Isolation And Ops Behavior

**Reuse Anchors**

- `src/mint/tests/test_issue_281_scheduler_and_healthz.py`
- `src/mint/tests/test_gateway_multi_target_routing.py`
- `src/mint/tests/test_client_compat_user_agent.py`

**Steps**

1. 明确 OpenPI 子系统故障时的隔离行为，优先保护现有 Mint 主路径。
2. 为 health/metrics/logging 补 OpenPI-specific labels，不改旧路径语义。
3. 对 route registration、config validation、runtime bridge、artifact path 建独立 tests，避免全部挤进旧测试文件。

**Commands**

```bash
cd src/mint && pytest \
  tests/test_issue_281_scheduler_and_healthz.py \
  tests/test_gateway_multi_target_routing.py \
  tests/test_client_compat_user_agent.py \
  tests/test_openpi_app_registration.py \
  tests/test_openpi_runtime_bridge.py -q
```

## Exit Criteria

- Mint 内存在显式 `tinker_server.openpi` package。
- OpenPI public routes、schemas、runtime bridge、config surface 都不依赖 `models/types.py` 的 token-only contract。
- 现有 Mint route family 和兼容测试保持稳定。

## Not In This Plan

- `mint.openpi.*` SDK
- OpenPI runtime implementation
- Cross-repo CI matrix
