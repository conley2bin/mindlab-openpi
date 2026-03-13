# OpenPI Contract Glossary

Glossary date: 2026-03-13

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
| generic training bridge | Mint 当前保留的低层 OpenPI training HTTP contract：`/api/v1/openpi/training/start`。它接受 config anchor 加少量 envelope 字段，直接桥接到 `openpi.run_training(...)`。 | `src/mint` | 它证明 OpenPI training facade 可被 Mint 调起，但它不是 Mint-native SFT 或未来 RL contract。 |
| isolated SFT contract | Mint 当前 OpenPI SFT HTTP/SDK contract：`/api/v1/openpi/training/sft/start` 和对应 `mint.openpi` SFT client surface。它以 config anchor 加 `TrainConfig` 白名单 override 组成。 | `src/mint` for service envelope; `src/mindlab-toolkit` for SDK decode | 它与 generic training bridge 分离；未来 RL contract 也必须保持同级隔离。 |
| SFT checkpoint alias | Mint 对外暴露的 SFT checkpoint URI 形状：`mint://openpi/sft/<config>/<exp>/<step>`。 | `src/mint` | 这是外部 alias，不要求底层持久化目录真的插入 `sft/`；Mint checkpoint resolver 会把它归一化回底层 OpenPI checkpoint tree。 |
| run uri | Mint service 与 Toolkit SDK 用于标识 OpenPI training run 的服务侧 URI，例如 `mint://openpi/<config>/<exp>`。 | `src/mint` for URI/envelope shape; `src/mindlab-toolkit` for SDK decode | 它是服务 contract，不是 OpenPI runtime 内部对象。 |
| client transport identity | SDK 发向 Mint service 时使用的 request-side transport identity，例如 `User-Agent`、auth header、request capability header、base URL 与 timeout policy。 | `src/mindlab-toolkit` | 不能无意复用现有 `Mint/Python ...` / Tinker-compatible identity 去触发 `src/mint/tinker_server/client_compat.py` 旧分支；它只描述客户端声明，不等于服务端已协商结果。 |
| negotiated capability signal | Mint OpenPI service 在 response header 中回传的当前 capability/version，例如 `X-Mint-OpenPI-Negotiated-Capability: 0.1`。 | response contract: `src/mint`; client validation: `src/mindlab-toolkit` | 它不是 SDK 自己发出的 request identity；它表示服务端实际回传的协商结果。 |
| capability skew detection | SDK 在看到 negotiated capability signal 后，把 client expectation 和 server actual value 做 fail-fast 比较。 | `src/mindlab-toolkit` | 当前策略是 “header present 则比较，header absent 则兼容”，不是要求所有历史服务立即升级。 |
| future | Mint service 用于异步任务轮询的 request id 与 retrieve contract。 | `src/mint` | 这是 service orchestration object，不是 OpenPI runtime semantic object。 |
| session | Mint 当前的通用服务端会话概念。 | `src/mint` | 不能默认等于 OpenPI episode。 |
| sampling session | Mint 当前 token-centric sampling lifecycle object。 | `src/mint` | 不能拿来直接表示 OpenPI policy lifecycle。 |
| episode | OpenPI runtime 中从 reset 到 complete 的环境交互区间。 | `src/openpi` | 不是 Mint sampling session 的同义词。 |
| reset | 把 policy 或 runtime 恢复到 episode 起点的动作。 | `src/openpi` | 不是 “删除 session” 或 “重新建模”的服务端近义词。 |
| action chunk | OpenPI policy 一次 inference 返回的一段动作序列。 | `src/openpi` | 不是 token 序列。 |
| observation | OpenPI policy 的结构化输入，可能包含 state、image、prompt 等多模态字段。 | `src/openpi` | 不是 Mint `ModelInput`。 |
| RLDS data loading | `src/openpi` 里针对 DROID 等数据集的 RLDS format loader/config。 | `src/openpi` | 这是 dataset/input pipeline 语义，不等于 RL reward/rollout/policy-update runtime。 |
| OpenPI RL runtime owner | 一个尚未落地的 upstream OpenPI facade，未来若存在，应显式拥有 rollout、reward/advantage、policy update 和 RL checkpoint contract。 | future owner must be `src/openpi` | 在这个 owner 出现前，Mint/Toolkit 不应长出 `mint.openpi` RL API。 |
| model input | Mint 当前 token/chunk 输入对象。 | `src/mint` | 只用于当前 Tinker-compatible path。 |
| compatibility matrix | 当前支持组合、验证锚点和未开始项的状态表。 | `docs/progress` | 不是未来愿景清单。 |
| validation baseline | 当前 hard gates、弱验证路径和归因口径。 | `docs/progress` | 不是测试实现文件本身。 |

## Ownership Rules

- `src/openpi` 定义 OpenPI semantic objects 和 runtime truth。
- `src/mint` 定义 service envelope、ops surface、polling、task orchestration。
- `src/mindlab-toolkit` 定义用户可见 naming、client ergonomics 和 package-level dependency choices。
- `src/mint` 拥有 response-side negotiated capability signal，`src/mindlab-toolkit` 拥有 request-side transport identity 和 skew detection。
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
- 不把 `RLDS*` dataset/config 误写成 OpenPI RL runtime owner。
- 不把 Mint 当前 `ppo` / `importance_sampling` / `rollout_correction_config` 直接命名成 OpenPI public contract。

## Terms That Stay Local

- `ModelInput`, `SampleRequest`, `SampleResponse`, `CreateSamplingSessionRequest` 继续只属于 Mint 当前 Tinker-compatible path。
- `Policy`, `ActionChunkBroker`, `create_trained_policy`, `reset()` 继续只属于 OpenPI runtime path。
- `apply_mint_patches()` 继续只属于 Toolkit 的现有 compatibility layer。
