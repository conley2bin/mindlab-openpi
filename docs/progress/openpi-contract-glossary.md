# OpenPI Contract Glossary

Glossary date: 2026-03-12

## Purpose

这份 glossary 统一三仓后续文档和实现里使用的术语。这里的定义是当前主线的工作定义。

## Terms

| Term | Working meaning | Canonical owner | Anti-confusion note |
| --- | --- | --- | --- |
| runtime surface | `src/openpi` 暴露给外部系统调用的 library-level API。它负责模型装配、policy lifecycle、artifact resolution、training entry contract。 | `src/openpi` | 不是 `scripts/serve_policy.py`，也不是 `openpi_client.runtime.Runtime` 的 environment episode loop。 |
| policy | 接受 structured observation，返回 action 或 action chunk 的对象。最小 interface 是 `infer(obs)`，可选 `reset()`。 | `src/openpi` | 不是 Mint 的 `SampleRequest` / `SampleResponse`。 |
| service contract | Mint 对外 HTTP API 的 request/response envelope、task orchestration、polling、auth、ops-visible metadata。 | `src/mint` | service contract 可以包装 OpenPI payload，但不能重新发明 OpenPI semantic object。 |
| SDK contract | 用户在 `mint.*` 或后续 `mint.openpi.*` 下看到的 public Python API。 | `src/mindlab-toolkit` | SDK contract 不是 runtime truth，也不是 service truth。 |
| artifact | checkpoint、assets、norm stats、训练输出、模型导出物及其引用方式。 | `src/openpi` for semantic meaning; `src/mint` for service-side proxy/envelope | Mint 可以代理 artifact，不拥有其 semantic definition。 |
| artifact reference | 指向 OpenPI artifact 的稳定引用对象或服务侧请求对象，例如 checkpoint URI、artifact resolve request/response。 | semantic meaning: `src/openpi`; service envelope: `src/mint`; SDK decode shape: `src/mindlab-toolkit` | 允许跨仓传递，但不允许三仓各自定义不同的 canonical meaning。 |
| checkpoint | 可用于恢复 inference 或 training state 的权重产物。 | `src/openpi` | 现有 Mint `mint://` / `tinker://` 路径只是服务侧 URI/envelope，不等于 OpenPI checkpoint truth。 |
| run uri | Mint service 与 Toolkit SDK 用于标识 OpenPI training run 的服务侧 URI，例如 `mint://openpi/<config>/<exp>`。 | `src/mint` for URI/envelope shape; `src/mindlab-toolkit` for SDK decode | 它是服务 contract，不是 OpenPI runtime 内部对象。 |
| client transport identity | SDK 发向 Mint service 时使用的 transport-level identity，例如 `User-Agent`、auth header、capability header、base URL 与 timeout policy。 | `src/mindlab-toolkit` | 不能无意复用现有 `Mint/Python ...` / Tinker-compatible identity 去触发 `src/mint/tinker_server/client_compat.py` 旧分支。 |
| future | Mint service 用于异步任务轮询的 request id 与 retrieve contract。 | `src/mint` | 这是 service orchestration object，不是 OpenPI runtime semantic object。 |
| session | Mint 当前的通用服务端会话概念。 | `src/mint` | 不能默认等于 OpenPI episode。 |
| sampling session | Mint 当前 token-centric sampling lifecycle object。 | `src/mint` | 不能拿来直接表示 OpenPI policy lifecycle。 |
| episode | OpenPI runtime 中从 reset 到 complete 的环境交互区间。 | `src/openpi` | 不是 Mint sampling session 的同义词。 |
| reset | 把 policy 或 runtime 恢复到 episode 起点的动作。 | `src/openpi` | 不是 “删除 session” 或 “重新建模”的服务端近义词。 |
| action chunk | OpenPI policy 一次 inference 返回的一段动作序列。 | `src/openpi` | 不是 token 序列。 |
| observation | OpenPI policy 的结构化输入，可能包含 state、image、prompt 等多模态字段。 | `src/openpi` | 不是 Mint `ModelInput`。 |
| model input | Mint 当前 token/chunk 输入对象。 | `src/mint` | 只用于当前 Tinker-compatible path。 |
| compatibility matrix | 当前支持组合、验证锚点和未开始项的状态表。 | `docs/progress` | 不是未来愿景清单。 |
| validation baseline | 当前 hard gates、弱验证路径和归因口径。 | `docs/progress` | 不是测试实现文件本身。 |

## Ownership Rules

- `src/openpi` 定义 OpenPI semantic objects 和 runtime truth。
- `src/mint` 定义 service envelope、ops surface、polling、task orchestration。
- `src/mindlab-toolkit` 定义用户可见 naming、client ergonomics 和 package-level dependency choices。
- `docs/progress/openpi-integration-baseline.md` 与 `docs/progress/openpi-validation-baseline.md` 记录 current truth、gate 分类和跨仓归因口径，但不拥有 semantic object definition。

## Naming Rules

- OpenPI-specific public surface 必须显式带 `openpi` 命名空间。
- `mint.openpi.*` 是新增 namespace，不是当前顶层 `mint.*` 的隐式改义。
- Mint 内 OpenPI service routes 必须放进独立 OpenPI family，不伪装成现有 token-only family 的扩展字段。

## Forbidden Conflations

- 不把 OpenPI observation/action payload 压扁成 Mint 当前 token prompt schema。
- 不把 `reset()` 解释成现有 sampling session reset 或 delete。
- 不把 `openpi_client.runtime.Runtime` 当成 Mint embedding contract。
- 不把 `mint.ServiceClient`、`mint.TrainingClient`、`mint.SamplingClient` 直接扩成 OpenPI client。
- 不把 Mint 的 `request_id` / `retrieve_future` 轮询对象误写成 OpenPI runtime semantic payload。
- 不在 Mint 或 Toolkit 里复制 OpenPI checkpoint/layout/norm stats 语义。

## Terms That Stay Local

- `ModelInput`, `SampleRequest`, `SampleResponse`, `CreateSamplingSessionRequest` 继续只属于 Mint 当前 Tinker-compatible path。
- `Policy`, `ActionChunkBroker`, `create_trained_policy`, `reset()` 继续只属于 OpenPI runtime path。
- `apply_mint_patches()` 继续只属于 Toolkit 的现有 compatibility layer。
