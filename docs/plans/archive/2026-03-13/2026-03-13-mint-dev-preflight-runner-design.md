# Mint Dev Preflight Runner Design

## Goal

为主仓库新增一个 repo-owned `mint-dev preflight runner`，把 `ssh mint-dev` 上的 generic service control-plane 预检固定成可复用、可测试、可文档化的入口。

这个 runner 只回答一件事：当前 `mint-dev` 上的 Mint dev server 和 detached queue control-plane 是否可用。它不是 OpenPI 语义验证器，不负责远端 deployment owner、checkpoint fixture、observation fixture，也不定义 SFT/RL 训练接口。

## Mapping To ST-08

它属于 `ST-08 Remote Deployment And Real-Checkpoint Validation` 的前置运维层。

原因不是它本身在做 remote OpenPI smoke，而是：

- 远端 OpenPI smoke 复用 `mint-dev` shared-cluster 环境时，必须先通过 generic queue control-plane probes
- 当前 `healthz ready` 不能单独证明 dev service 可用
- 这条基线如果不沉淀成 repo-owned runner，后续 remote smoke 失败会持续在 deployment / service / queue 三层之间混淆

## Four Work Lines

### 1. Mint Dev Preflight Runner

- Owner: 主仓库 root
- Purpose: 验证 `mint-dev` host、HTTP process、detached queue control-plane
- Inputs: `ssh` host、base URL、log path、poll timeout
- Outputs: 结构化 preflight report 和明确退出码
- Dependency shape: 只依赖 `mint-dev` 当前环境，不依赖外部 base URL、checkpoint、OpenPI observation fixture

### 2. Remote Smoke / URL Validation

- Owner: `src/mint`
- Current entry: `src/mint/scripts/tools/openpi_remote_smoke.py`
- Purpose: 验证 deployed Mint OpenPI HTTP surface
- Hard blockers: stable deployment owner、stable base URL、real checkpoint fixture、matching observation fixture
- Relation to preflight: 如果 remote lane 复用 `mint-dev` shared-cluster，应先跑 preflight，再归因 OpenPI 路由失败

### 3. Mint-Native SFT API

- Owner: `src/mint` + `src/mindlab-toolkit` + `src/openpi`
- Purpose: 为 research users 暴露 OpenPI-specific SFT 参数接口
- Boundary: 保持现有 `/api/v1/openpi/training/start` 兼容桥；新增 isolated OpenPI-specific routes，不污染其他 Mint 模型族
- Not part of this runner

### 4. Mint-Native RL API

- Owner: `src/mint` + `src/mindlab-toolkit` + `src/openpi`
- Purpose: 暴露 OpenPI-specific RL 训练参数接口
- Boundary: 与 SFT 一样，隔离在 OpenPI-specific surface 内
- Not part of this runner

推荐顺序保持不变：

1. 先补 `mint-dev preflight runner`
2. 再把它接到 remote smoke / URL validation 线
3. 再展开 Mint-native SFT API
4. 最后做 RL API

## Options Considered

### Option A: 只保留技能文档，不写 runner

- 优点: 实现成本最低
- 问题: 无法形成稳定 CLI 入口；每次都要手工拼命令；不能写单元测试；运维知识仍然分散在 skill 和会话里

### Option B: 主仓库本地 orchestrator，通过 `ssh mint-dev` 执行远端 stdlib probe

- 优点: owner 正确；不依赖 `src/mint` 子模块脚本；本地只依赖 Python 标准库；可以输出结构化 JSON；可以单元测试 SSH 输出解析和状态归类；默认不做 restart / actor kill
- 问题: 需要维护一段嵌入式远端 probe 代码；需要处理 SSH banner / stdout 噪声

### Option C: 把 preflight 写进 `src/mint/scripts/tools`

- 优点: 靠近现有 issue repro scripts
- 问题: owner 错误；这不是 Mint 子模块私有逻辑，而是主仓库 ST-08 运维入口；继续堆在 `src/mint` 会把 root skills 和 root docs 再次降级成转发层

推荐 `Option B`。

## Proposed Design

### Location

- Script: `scripts/tools/mint_dev_preflight.py`
- Tests: `tests/test_mint_dev_preflight.py`

### Execution Model

本地 runner 负责：

- 组装非交互 `ssh -o BatchMode=yes -o ConnectTimeout=<n> mint-dev ...` 命令
- 传入远端 probe 配置
- 解析远端返回的单行 JSON report
- 渲染人类可读摘要或 `--json` 输出
- 根据 report 分类设置进程退出码
- 对本地 `ssh` 子进程设置总超时，避免卡在 host-key prompt、auth prompt 或网络 stall

远端 probe 负责：

- 采集 `hostname`、`whoami`
- 解析 `/root/tinker_project/tinker-server` symlink
- 检查 `run_server.py` 进程
- tail `/tmp/tinker_server.log`
- 调 `GET /api/v1/healthz`
- 调 `GET /internal/work_queue/debug_state`
- 调 `POST /internal/work_queue/noop`
- 轮询 `POST /api/v1/retrieve_future`

### Why Run The HTTP Checks On The Remote Host

- 目标就是验证 `mint-dev` 上 host-local service 当前状态
- 避免要求本机预先建立 SSH tunnel
- 让输出直接对应 `mint-dev` 视角的连接错误和 HTTP 状态

### Mutation Policy

默认不做：

- server restart
- actor recycle
- raylet attach
- cluster mutation

默认会做一次 `internal.noop` enqueue 和 `retrieve_future` poll。

这不是纯只读，但它是当前最小控制平面验证链的一部分，而且不会改变模型状态、部署配置或远端文件。

### Output Contract

默认文本输出应包含：

- overall state
- ssh host
- server root symlink target
- whether `run_server.py` was observed
- `healthz` result
- `debug_state` result
- `noop` request id
- `retrieve_future` terminal result

`--json` 输出应包含：

- `overall_state`
- `exit_code`
- `ssh_host`
- `base_url`
- `steps`
- `observations`
- `request_id` when noop succeeded

### Exit Codes

- `0`: preflight passes through queue chain
- `10`: SSH / remote bootstrap failure, including connect timeout, auth/prompt stall, local `ssh` spawn failure or remote bootstrap failure without a sentinel report
- `20`: server unavailable or `healthz` failed
- `30`: queue control-plane failed at `debug_state` / `noop` / `retrieve_future`
- `40`: malformed remote output or internal runner error

### Step Classification

- `host_identity`, `server_root`, `server_process`, `server_log_tail` 是诊断上下文
- `healthz` 是 server liveness gate
- `debug_state`, `noop`, `retrieve_future` 是 queue control-plane gate

只要 `healthz` 未通过，就不把后续问题写成 OpenPI-specific failure。

## Verification Plan

### Unit-Level

- 测 `ssh` 命令组装
- 测 SSH stdout 中 report sentinel 提取
- 测 exit code 分类
- 测默认文本渲染
- 测 `--json` 输出

### Script-Level

- 本地 `--dry-run` 验证命令组装
- 用 mocked `subprocess.run` 验证 SSH failure、remote malformed output、queue pass 三条路径

### Environment-Level

- 对真实 `ssh mint-dev` 运行一次 preflight
- 只接受 read-only / low-impact 行为，不做 restart
- 把观测到的当前结果回写到 `docs/progress`
- 不把 restart、raylet join、actor recycle 或特定 head IP 的历史手工调试结果提升成这个 slice 的当前 hard fact；这些都要单独重验

## Consequences

落地后，`ST-08` 会形成清晰的两层前置关系：

- 第 1 层：`mint-dev preflight runner` 验证 generic service control-plane
- 第 2 层：`src/mint/scripts/tools/openpi_remote_smoke.py` 验证 OpenPI-specific deployed HTTP surface

这样后续 SFT/RL 接口扩张时，不需要再把 generic queue、dev host、URL reachability 和 OpenPI contract 失败混成一个问题。
