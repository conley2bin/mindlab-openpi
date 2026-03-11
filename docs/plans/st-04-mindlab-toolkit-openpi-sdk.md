# ST-04 Mindlab Toolkit OpenPI SDK Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `src/mindlab-toolkit` 中新增显式 `mint.openpi.*` namespace，让用户能调用 Mint 的 OpenPI service surface，同时保持现有 `mint.*` 和 `mint.tinker.*` compatibility contract 不变。

**Architecture:** 先保住现有 namespace 和 patch side effects，再新增 `mint.openpi` 子包。OpenPI SDK 不伪装成 `tinker` client，也不通过顶层 re-export 偷偷改义。首个版本只做 Mint service client，不要求替代 `openpi-client` 的直接 runtime client 生态。当前 `mint` 包导入时总会执行 `apply_mint_patches()` 并校验 `tinker==0.6.0`；首个 `mint.openpi` cut 暂时接受这层包级耦合，但它只是临时约束，不是长期 contract，本计划不在这一轮重写顶层 import graph。

**Tech Stack:** Python packaging, `httpx`-style explicit HTTP client or equivalent transport, pytest

---

## Existing Repo Anchors

- `src/mindlab-toolkit/src/mint/__init__.py` 当前导入时会先执行 `apply_mint_patches()`，然后把 `mint.tinker` 大量 re-export 到顶层。
- `src/mindlab-toolkit/src/mint/tinker/__init__.py` 当前是显式 Tinker-compatible export list。
- `src/mindlab-toolkit/src/mint/mint/__init__.py` 当前 patch layer 会修改 `tinker` 的 client init、sampling session path、future polling、telemetry。
- `src/mindlab-toolkit/tests/test_namespace_contract.py` 锁定顶层 re-export 和版本语义。
- `src/mindlab-toolkit/tests/test_mint_polling_patch.py` 锁定 patch behavior。
- Cross-repo contract anchor: `src/mint/tinker_server/client_compat.py` 会根据 User-Agent 选择旧 `tinker://` / `mint://` checkpoint URI 行为，`mint.openpi` 不能无意触发它。

## Temporary Constraint

- 当前 `mint.openpi` 首个 cut 仍然处于 `import mint` 的包级导入链下，因此会跟随现有 `apply_mint_patches()` 和 `tinker==0.6.0` version guard 一起发生。
- 这只是当前包结构的临时约束，不应被解释成长期 public contract。
- 后续如果 OpenPI surface 稳定，必须单独判断是否允许 `mint.openpi` 在不加载旧 patch stack 的情况下导入。

## Must-Pass Existing Regression Anchors

```bash
cd src/mindlab-toolkit && pytest \
  tests/test_namespace_contract.py \
  tests/test_mint_polling_patch.py -q
```

新增 OpenPI SDK 前后，这组测试都必须不改断言地继续通过。

## Required Packaging Decision

当前 `src/mindlab-toolkit/pyproject.toml` 只有 `tinker==0.6.0` 依赖，没有通用 HTTP client。`mint.openpi` 不能假装继续复用 `tinker` token-centric generated client。首个 SDK cut 必须显式做一个依赖决策：

- 方案 A: 在 Toolkit 内新增 `httpx` 之类的轻量 HTTP client 依赖，直接调用 Mint OpenPI service surface。
- 方案 B: 引入单独的 Mint OpenPI client package。

本计划默认采用方案 A。不要让 `mint.openpi` 依赖 `openpi-client` 的 websocket/policy abstractions。

## Recommended Package Layout

- `src/mindlab-toolkit/src/mint/openpi/__init__.py`
- `src/mindlab-toolkit/src/mint/openpi/config.py`
- `src/mindlab-toolkit/src/mint/openpi/types.py`
- `src/mindlab-toolkit/src/mint/openpi/client.py`

## Phase 1: Reserve The Namespace Without Changing Existing Behavior

**Create**

- `src/mindlab-toolkit/src/mint/openpi/__init__.py`
- `src/mindlab-toolkit/tests/test_openpi_namespace_contract.py`

**Modify**

- `src/mindlab-toolkit/src/mint/__init__.py`

**Steps**

1. 顶层 `mint` 只显式暴露 `mint.openpi` 子命名空间，不 re-export OpenPI client symbols 到顶层。
2. `mint.openpi` 的导入不能改变 `apply_mint_patches()` 的现有行为。
3. 旧的 `mint.*`、`mint.tinker.*`、`mint.mint.*` relationship 保持不变。
4. `test_namespace_contract.py` 保持原样；OpenPI namespace 约束放进新测试文件。

**Commands**

```bash
cd src/mindlab-toolkit && pytest \
  tests/test_namespace_contract.py \
  tests/test_mint_polling_patch.py \
  tests/test_openpi_namespace_contract.py -q
```

**Gate**

- `mint.openpi` 存在。
- 顶层 `mint.ServiceClient`、`mint.TrainingClient`、`mint.SamplingClient` 的身份关系不变。

## Phase 2: Add Transport And Config Surface Explicitly

**Modify**

- `src/mindlab-toolkit/pyproject.toml`
- `src/mindlab-toolkit/src/mint/openpi/config.py`

**Steps**

1. 为 `mint.openpi` 增加显式 transport dependency，而不是偷偷借用 `tinker` 的 token client internals。
2. 显式定义 `mint.openpi` 的 transport identity，包括 User-Agent/header strategy；默认不要复用 `Mint/Python`，避免误触 Mint 现有 Tinker-compatible heuristics。
3. 定义 OpenPI service base URL、auth、timeout、polling policy 等 config objects。
4. 把 Mint version、Tinker compatibility version、OpenPI capability version 分开表达，不混在 `__version__` 里。

**Commands**

```bash
cd src/mindlab-toolkit && python -m pytest \
  tests/test_namespace_contract.py \
  tests/test_openpi_namespace_contract.py -q
```

**Gate**

- `pyproject.toml` 里的 transport dependency 决策已经落地。
- config objects 与现有 `mint.mint` env patching 语义隔离。
- OpenPI client identity 不会无意满足 `is_tinker_sdk_user_agent()`。

## Phase 3: Define OpenPI Types And Client

**Create**

- `src/mindlab-toolkit/src/mint/openpi/types.py`
- `src/mindlab-toolkit/src/mint/openpi/client.py`
- `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`

**Steps**

1. `types.py` 反映 `ST-03` 的 OpenPI service schema，而不是复制 `tinker` token types。
2. `client.py` 只封装 Mint OpenPI service surface，不复制 OpenPI runtime logic。
3. `mint.openpi` 先暴露最小 stable surface:
   - inference call
   - task/future query
4. training methods 和 artifact query 等到 `ST-03` 对应服务面稳定后再暴露，不提前占位。

**Commands**

```bash
cd src/mindlab-toolkit && pytest \
  tests/test_openpi_namespace_contract.py \
  tests/test_openpi_sdk_contract.py -q
```

**Gate**

- `mint.openpi` 的 public names 体现 OpenPI observation/action 语义，不模仿 `SamplingClient`。
- SDK 只依赖 Mint service contract，不直接依赖 `src/openpi` 内部实现。
- SDK 首个 stable surface 只依赖 `ST-03` 已经落地的 inference path 和 task/future query path。

## Phase 4: Keep Patch Side Effects Contained

**Reuse Anchors**

- `src/mindlab-toolkit/tests/test_mint_polling_patch.py`

**Steps**

1. 验证 `mint.mint.apply_mint_patches()` 仍只影响旧兼容层。
2. 明确 `mint.openpi` 不自动继承这些 patch assumptions，除非服务协议明确需要。
3. 避免为了少写代码，把 `mint.openpi` 客户端构建在当前 monkey-patched `tinker` clients 之上。

**Commands**

```bash
cd src/mindlab-toolkit && pytest \
  tests/test_mint_polling_patch.py \
  tests/test_openpi_sdk_contract.py -q
```

**Gate**

- OpenPI SDK 引入后，patch tests 不出现新副作用。

## Phase 5: Publish Only Stable Surface

**Modify**

- `src/mindlab-toolkit/README.md`

**Steps**

1. README 只写已经稳定的 `mint.openpi` 用法。
2. 对已有直接使用 `openpi-client` 的用户，保留并列路径，不宣称强制迁移。
3. 不把实验性 helper 写入 `__all__`。

## Exit Criteria

- Toolkit 内存在显式 `mint.openpi` package。
- 新 SDK 不改变现有 `mint.*` / `mint.tinker.*` contract。
- `pyproject.toml` 已处理 transport dependency，而不是把 SDK 实现悬空。

## Not In This Plan

- Mint service route implementation
- OpenPI runtime implementation
- Full migration guide from `openpi-client`
