# ST-02 OpenPI Runtime Surface Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `src/openpi` 内提炼一层 Mint 可依赖的 integration-facing runtime surface，使 Mint 调用的是稳定库接口，不是脚本拼装、websocket server 或研究期 helper。

**Architecture:** 先做 inference/runtime facade，再做 artifact facade，最后才把 training facade 和脚本入口收敛过去。不要一开始就把 inference、training、serving 三条历史路径强行统一成一个大抽象。`openpi_client.runtime.Runtime` 是 environment episode loop，不是 Mint embedding contract，不能把它误当成服务端集成入口。

**Tech Stack:** Python, JAX, PyTorch, pytest, `uv`, package layout under `src/openpi/src/openpi/`

---

## Existing Repo Anchors

- `src/openpi/src/openpi/policies/policy.py` 已经定义了 `infer(obs)`、`metadata` 和 JAX/PyTorch 双实现分支。
- `src/openpi/src/openpi/policies/policy_config.py` 已经负责 checkpoint download、backend detection、transform assembly。
- `src/openpi/scripts/serve_policy.py` 是当前 inference 装配入口。
- `src/openpi/scripts/train.py` 和 `src/openpi/scripts/train_pytorch.py` 是当前 training 装配入口。
- `src/openpi/src/openpi/training/checkpoints.py`、`src/openpi/src/openpi/training/weight_loaders.py` 持有 artifact truth。
- `src/openpi/packages/openpi-client/src/openpi_client/base_policy.py` 是最小 policy interface。
- `src/openpi/packages/openpi-client/src/openpi_client/action_chunk_broker.py` 是当前 action chunk lifecycle 适配器。
- `src/openpi/packages/openpi-client/src/openpi_client/websocket_client_policy.py` 是 remote inference client adapter，不是 Mint embedding contract。
- `src/openpi/packages/openpi-client/src/openpi_client/runtime/runtime.py` 是 runtime loop reference，不是 Mint 集成 API。

## Test Anchor Classification

**Must-pass local anchors**

- `cd src/openpi && uv run pytest --strict-markers -m "not manual" src/openpi/models/model_test.py -q`
- `cd src/openpi && uv run pytest src/openpi/models/lora_test.py -q`
- `cd src/openpi && uv run pytest scripts/train_test.py -q`

**Exploratory or network-dependent anchors**

- `src/openpi/src/openpi/models/model_test.py::test_model_restore` 标记为 `manual`
- `src/openpi/src/openpi/policies/policy_test.py` 标记为 `manual`
- `src/openpi/src/openpi/shared/download_test.py` 依赖远端资源

当前仓库还没有 deterministic 的 inference facade hard gate。`ST-02` Phase 1 必须先补这一层，不能把 Mint 集成硬绑到 manual 或远端 checkpoint 测试上。

## Recommended Package Layout

- `src/openpi/src/openpi/integration/__init__.py`
- `src/openpi/src/openpi/integration/runtime.py`
- `src/openpi/src/openpi/integration/artifacts.py`
- `src/openpi/src/openpi/integration/training.py`
- `src/openpi/src/openpi/integration/errors.py`

## Phase 1: Introduce An Inference Runtime Facade

**Create**

- `src/openpi/src/openpi/integration/__init__.py`
- `src/openpi/src/openpi/integration/runtime.py`
- `src/openpi/src/openpi/integration/errors.py`
- `src/openpi/src/openpi/integration/runtime_test.py`

**Modify**

- `src/openpi/src/openpi/policies/policy_config.py`
- `src/openpi/src/openpi/__init__.py`

**Steps**

1. 定义 Mint-facing inference handle，至少显式覆盖 `load`, `infer`, `reset`, `metadata` 四个能力。
2. 把 checkpoint resolution、model backend detection、transform stack assembly 从 `policy_config.py` 收敛到 facade 后面。
3. 保持 facade 输入输出仍是 OpenPI observation/action/multimodal 语义，不引入 token prompt wrapper。
4. 明确 facade 与 `BasePolicy` / `ActionChunkBroker` 的关系：Mint 依赖 integration handle，不直接依赖 websocket client/server，但 action chunk lifecycle 不能在 facade 里被抹平。
5. 明确错误边界，至少区分 checkpoint missing、asset missing、unsupported backend、invalid observation shape。
6. 为 facade 写本地可跑 contract tests，使用 fake config/fake observation，不依赖远端 checkpoint。

**Commands**

```bash
cd src/openpi && uv run pytest --strict-markers -m "not manual" src/openpi/models/model_test.py -q
cd src/openpi && uv run pytest src/openpi/integration/runtime_test.py -q
```

**Gate**

- `integration/runtime.py` 可以独立于 websocket server 被调用。
- `runtime_test.py` 不依赖 `manual` marker 或远端资源。
- `src/openpi/models/model_test.py::test_model_restore` 不再被当成 facade 的 deterministic proof。
- `policy_test.py` 仍然只是 exploratory lane，不充当唯一 contract proof。

## Phase 2: Introduce An Artifact Facade

**Create**

- `src/openpi/src/openpi/integration/artifacts.py`
- `src/openpi/src/openpi/integration/artifacts_test.py`

**Modify**

- `src/openpi/src/openpi/policies/policy_config.py`
- `src/openpi/src/openpi/training/checkpoints.py`
- `src/openpi/src/openpi/training/weight_loaders.py`

**Steps**

1. 把 checkpoint path resolution、norm stats loading、released checkpoint vs training checkpoint 差异收敛到 artifact facade。
2. 定义 Mint 需要看到的 artifact reference，而不是让 Mint 直接猜 `params/`、`assets/`、`model.safetensors` 目录语义。
3. 明确哪些 artifact errors 原样抛出，哪些在 OpenPI 内先标准化。
4. 保持 artifact truth 仍留在 `src/openpi`，不要把目录规则复制到 Mint。

**Commands**

```bash
cd src/openpi && uv run pytest src/openpi/models/lora_test.py -q
cd src/openpi && uv run pytest src/openpi/integration/artifacts_test.py -q
```

**Gate**

- Mint 不需要再硬编码 OpenPI checkpoint 目录结构。
- artifact tests 覆盖 released checkpoint 和 training checkpoint 两条路径。

## Phase 3: Introduce A Training Facade Without Over-Unifying Backends

**Create**

- `src/openpi/src/openpi/integration/training.py`
- `src/openpi/src/openpi/integration/training_test.py`

**Modify**

- `src/openpi/scripts/train.py`
- `src/openpi/scripts/train_pytorch.py`
- `src/openpi/src/openpi/training/config.py`

**Steps**

1. 定义 callable training entry contract，而不是继续让 `scripts/train.py` 成为唯一 API。
2. JAX 和 PyTorch 后端共用 entry contract，但保留 backend-specific adapter；不要为了表面统一抹平真实差异。
3. 把 debug training path 作为首个 hard gate，先保证本地最小训练闭环能走通。
4. 明确 training handle 暴露哪些状态给 Mint，哪些仍属于 OpenPI 内部训练细节。

**Commands**

```bash
cd src/openpi && uv run pytest scripts/train_test.py -q
cd src/openpi && uv run pytest src/openpi/integration/training_test.py -q
```

**Gate**

- `train.py` 和 `train_pytorch.py` 不再持有 canonical integration contract。
- training facade 能表达 “start / resume / artifact output / failure” 最小闭环。

## Phase 4: Turn Existing Scripts Into Adapters

**Modify**

- `src/openpi/scripts/serve_policy.py`
- `src/openpi/scripts/train.py`
- `src/openpi/scripts/train_pytorch.py`

**Steps**

1. `serve_policy.py` 只负责 CLI 参数解析和 websocket adapter，不再负责 canonical policy assembly。
2. `train.py` 和 `train_pytorch.py` 只负责 CLI/config translation，不再定义 Mint 依赖的 runtime contract。
3. 明确 `openpi_client.websocket_client_policy` 与 `websocket_policy_server.py` 只是 remote adapter 路径。

**Commands**

```bash
cd src/openpi && uv run python scripts/serve_policy.py --help
cd src/openpi && uv run pytest scripts/train_test.py -q
```

**Gate**

- 脚本仍可供研究工作流使用。
- Mint 后续依赖 `openpi.integration.*`，不依赖脚本文件或 websocket server class。

## Phase 5: Export Only The Stable Surface

**Modify**

- `src/openpi/src/openpi/__init__.py`
- `src/openpi/README.md`

**Steps**

1. 只导出已经被 tests 锁住的 integration surface。
2. 不把研究期 helper、internal adapters、manual test hooks 公开成 Mint 依赖面。
3. README 只记录已经稳定的 integration-facing entry，不记录内部重构历史。

**Gate**

- `src/openpi` 对外有单一、显式、可测试的 integration package。

## Exit Criteria

- `src/openpi/src/openpi/integration/` 存在并承载 inference、artifact、training 三类 facade。
- `scripts/serve_policy.py`、`scripts/train.py`、`scripts/train_pytorch.py` 已经退回 adapter 角色。
- Mint 后续可以只依赖 `openpi.integration.*`，不追逐 `policies/`、`scripts/`、`serving/` 内部重构。

## Not In This Plan

- Mint route design
- Toolkit SDK naming
- Cross-repo closed-loop validation
