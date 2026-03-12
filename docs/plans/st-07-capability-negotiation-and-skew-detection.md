# ST-07 Capability Negotiation And Skew Detection Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 Mint OpenPI service 增加 response-side capability signal，并让 Toolkit SDK 在发现 capability/version mismatch 时 fail-fast。

**Architecture:** 保持当前 payload schema 稳定，第一刀只新增 response-side negotiated capability header。Mint 负责返回协商信号，Toolkit 负责读取并在 mismatch 时抛出显式错误；旧服务在未返回该 header 时继续按现状工作。

**Tech Stack:** FastAPI, httpx, pytest, Markdown

---

## Boundary Inputs

- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-integration-baseline.md`
- `docs/progress/openpi-contract-glossary.md`

This plan inherits these rules:

- `src/mint` 拥有 service contract
- `src/mindlab-toolkit` 拥有 SDK ergonomics 和 fail-fast 行为
- 第一刀只做 additive contract，不破坏现有 JSON payload 形状

## Deliverables

- `src/mint/tinker_server/openpi/routes.py`
- `src/mint/tests/test_openpi_runtime_bridge.py`
- `src/mindlab-toolkit/src/mint/openpi/client.py`
- `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`
- Updated `docs/progress/openpi-compatibility-matrix.md`
- Updated `docs/progress/openpi-integration-baseline.md`
- Updated `docs/progress/openpi-contract-glossary.md`

## Phase 1: Mint Returns A Response-Side Negotiated Capability Signal

**Modify**

- `src/mint/tinker_server/openpi/routes.py`
- `src/mint/tests/test_openpi_runtime_bridge.py`

**Steps**

1. 在 Mint OpenPI route family 内定义服务端当前协商 capability version 常量。
2. 为 public/internal status 以及当前 public OpenPI routes 返回同一个 response-side negotiated capability header。
3. 写 route-level failing test，证明 status 和至少一条行为性 route 会返回该 header。
4. 运行 Mint targeted tests，确认新增 header 不改变现有 payload 语义。

## Phase 2: Toolkit Fails Fast On Capability Mismatch

**Modify**

- `src/mindlab-toolkit/src/mint/openpi/client.py`
- `src/mindlab-toolkit/tests/test_openpi_sdk_contract.py`

**Steps**

1. 写 failing test：当 response-side negotiated capability header 存在且与 client config 不匹配时，SDK 抛出 `OpenPIClientError`。
2. 写 failing test：当 header 匹配时，现有 infer/status/download/training path 继续正常工作。
3. 在 SDK client 中集中解析该 header，避免每个 API method 各自复制一套逻辑。
4. 保持对旧服务的兼容：当 header 缺失时，不主动把旧服务全部判成错误。

## Phase 3: Sync Docs To Current Truth

**Modify**

- `docs/progress/openpi-compatibility-matrix.md`
- `docs/progress/openpi-integration-baseline.md`
- `docs/progress/openpi-contract-glossary.md`

**Steps**

1. 把 “response-side negotiated signal missing” 改成当前事实。
2. 明确 request-side identity、response-side negotiated signal 和 client-side skew detection 的 owner。
3. 保留 remote deployment smoke outside localhost 为后续缺口，不和 `ST-07` 混写。

## Exit Criteria

- Mint OpenPI routes 返回 response-side negotiated capability signal。
- Toolkit SDK 在 mismatch 时 fail-fast，在 header 缺失时保持向后兼容。
- 相关 docs/progress 与 docs/targets 不再把 response-side signal 写成缺失。
