# Mint Dev Preflight Runner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在主仓库新增一个 repo-owned `mint-dev` preflight runner，用统一 CLI 检查 dev host、Mint HTTP server 和 detached queue control-plane。

**Architecture:** runner 放在主仓库 `scripts/tools/`，本地通过 `ssh mint-dev` 执行远端标准库 probe，远端 probe 负责采集 host/process/log/HTTP 状态并返回单行 JSON report；本地只负责解析、渲染和退出码分类。默认不做 restart 或 actor recycle，但会执行最小 queue validation 链：`healthz`、`debug_state`、`noop`、`retrieve_future`。

**Tech Stack:** Python 3 stdlib, pytest, Markdown

**Status:** 已实现。这份文件现在作为后续维护这条 slice 的回归清单，不再假设文件尚未存在。

---

### Task 1: Extend Runner Tests First

**Files:**
- Modify: `tests/test_mint_dev_preflight.py`

**Step 1: Add the failing test for the next behavior change**

```python
def test_extract_report_from_ssh_output_uses_prefixed_json_line():
    payload = extract_report_from_ssh_output("banner\nMINT_DEV_PREFLIGHT_REPORT={\"overall_state\":\"pass\"}\n")
    assert payload["overall_state"] == "pass"
```

继续补几类测试：

- `plan_ssh_command()` 会生成 `ssh <host> ... python3 - ...`
- 找不到 sentinel line 时抛错误
- `determine_exit_code()` 区分 `server_unavailable` 和 `queue_unhealthy`
- `render_text_report()` 会输出 overall state 和关键 step
- `main()` 的 `--json`、`ssh_failure`、malformed output 和 non-dry-run path 都要有 mocked `subprocess.run` 覆盖

**Step 2: Run test to verify it fails for the intended reason**

Run: `python3 -m pytest tests/test_mint_dev_preflight.py -q`

Expected: FAIL with assertion mismatch or missing behavior, not import errors

**Step 3: Commit**

等 Task 2 完成后一并提交。

### Task 2: Maintain The Root Runner Contract

**Files:**
- Modify: `scripts/tools/mint_dev_preflight.py`

**Step 1: Write minimal implementation**

实现这些最小单元：

- `plan_ssh_command(...)`
- `extract_report_from_ssh_output(...)`
- `determine_exit_code(...)`
- `render_text_report(...)`
- `main(...)`

远端 probe 逻辑保持在脚本内部常量字符串里，输出固定 sentinel：

```python
print("MINT_DEV_PREFLIGHT_REPORT=" + json.dumps(report, sort_keys=True))
```

本地 runner 只接受这一行作为 machine-readable source of truth。

**Step 2: Run targeted tests**

Run: `python3 -m pytest tests/test_mint_dev_preflight.py -q`

Expected: PASS

**Step 3: Run dry-run verification**

Run: `python3 scripts/tools/mint_dev_preflight.py --dry-run`

Expected: 输出带 `BatchMode=yes` 与 `ConnectTimeout` 的 `ssh mint-dev ...` 命令，不访问远端

**Step 4: Commit**

```bash
git add tests/test_mint_dev_preflight.py scripts/tools/mint_dev_preflight.py
git commit -m "feat: add mint-dev preflight runner"
```

### Task 3: Re-Verify On Real Mint Dev And Sync Docs

**Files:**
- Modify: `docs/progress/openpi-validation-baseline.md`
- Modify: `docs/progress/openpi-integration-baseline.md`
- Modify: `docs/progress/openpi-compatibility-matrix.md`
- Modify: `docs/targets/subtarget-08-remote-deployment-and-real-checkpoint-validation.md`

**Step 1: Run live preflight**

Run: `python3 scripts/tools/mint_dev_preflight.py --json`

Expected:

- SSH succeeds
- report includes host identity, server root, process observation
- if queue chain passes, exit code `0`
- if queue chain fails, output shows exact failing step and exit code `20` or `30`

**Step 2: Update docs with current truth**

- progress 文档记录 runner 已存在、属于 root-owned preflight gate、位于 remote smoke 前
- progress / skill 文档把历史手工运维观察和本次 preflight 证据分开，避免把旧 head IP、旧 runtime 或 restart 结果写成当前 hard fact
- `ST-08` target 文档记录这个新入口和它的 boundary
- 结构不变时，不修改 `docs/targets/target.md` 的状态表

**Step 3: Re-run checks**

Run:

```bash
python3 -m pytest tests/test_mint_dev_preflight.py -q
python3 scripts/tools/mint_dev_preflight.py --dry-run
python3 scripts/tools/mint_dev_preflight.py --json
rg -n "^## 子目标总表|^\\| ST-|^## Current Status|^- Status:" docs/targets/target.md docs/targets/subtarget-*.md
```

Expected:

- tests pass
- dry-run prints command
- live run emits a structured report
- target structure remains consistent

**Step 4: Commit**

```bash
git add docs/progress/openpi-validation-baseline.md \
        docs/progress/openpi-integration-baseline.md \
        docs/progress/openpi-compatibility-matrix.md \
        docs/targets/subtarget-08-remote-deployment-and-real-checkpoint-validation.md
git commit -m "docs: record mint-dev preflight gate"
```
