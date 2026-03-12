---
name: write-daily-report
description: Use when writing a daily work report from repository evidence bounded by commit range, especially when the report must continue from the previous daily report's range_end_commit to current HEAD, or bootstrap from a manually provided start commit.
---

# Write Daily Report

## Overview

Write one report from committed repository facts:
- `docs/daily-report/YYYY-MM-DD.md`

The collector defines the commit boundary. The model groups facts into themes, runs the smallest relevant verification commands, and writes one concrete, plain-language report.

## Workflow

1. Determine the target date.
   - The filename date is the day the report is generated.
   - Default to today.
   - Use `YYYY-MM-DD`.

2. Collect facts.

Automatic continuation:

```bash
python3 .codex/skills/write-daily-report/scripts/collect_daily_report_facts.py \
  --date 2026-03-12 \
  --repo-root /absolute/path/to/repo \
  --json-indent 2
```

Bootstrap or missing-boundary case:

```bash
python3 .codex/skills/write-daily-report/scripts/collect_daily_report_facts.py \
  --date 2026-03-12 \
  --start-commit 657117afc7316b8aebf0d807c9b6cc54513e7314 \
  --repo-root /absolute/path/to/repo \
  --json-indent 2
```

3. Read the JSON output and treat it as the only fact source for prose.
   - `range_start_commit`, `range_end_commit`: machine-readable report boundary
   - `range_start_author_date`, `range_end_author_date`: human-readable author timestamps for the boundary commits
   - `commits`: committed changes inside the resolved range
   - `code_evidence`: code-first evidence extracted from changed files, changed tests, submodule gitlink ranges, and inferred capability buckets
   - `progress_docs`: committed updates under `docs/progress/`, `docs/targets/`, and `docs/plans/` touched by that range
   - `facts`: prose-ready facts from code evidence, progress docs, selected current-state target docs, and commit subjects
   - `verification_commands`: candidate commands extracted from docs and changed tests

4. Build 3 to 6 work themes.
   - Group by capability chain, not by repository name.
   - Prefer `code_evidence` over progress-doc facts.
   - Use progress-doc facts only to explain why the code change matters or what gap remains.
   - Use commit subjects only when neither code evidence nor docs say enough.
   - Do not create a theme unless it has at least one concrete anchor.

5. Select the smallest relevant verification commands.
   - Run 1 to 2 commands per theme when possible.
   - Prefer commands that directly test the capability described by that theme.
   - For pytest commands, prefer detailed output such as `-vv -ra`, not `-q`.
   - Priority order:
     1. explicit commands from progress/plan/target docs
     2. commands derived from changed test files in `code_evidence`
     3. no command; mark the screenshot placeholder as manual
   - Do not run full test suites unless the collector found no narrower command.

6. Write `docs/daily-report/YYYY-MM-DD.md`.
   - The file must start with this YAML front matter:

```yaml
---
range_start_commit: <sha>
range_start_author_date: <YYYY-MM-DD HH:MM:SS +08:00>
range_end_commit: <sha>
range_end_author_date: <YYYY-MM-DD HH:MM:SS +08:00>
---
```

## Fact Boundary

Use only:
- committed changes in the resolved commit range
- committed updates in `docs/progress/` touched by that range
- committed updates in `docs/targets/` touched by that range
- committed updates in `docs/plans/` touched by that range
- fresh output from the selected verification commands

Do not use:
- uncommitted working-tree changes
- memory of previous conversations
- unstated intent
- manual guesses about why something happened

Continuation rules:
- automatic continuation reads only `docs/daily-report/YYYY-MM-DD.md`
- the latest daily report before the target date supplies `range_end_commit`
- if no previous daily report exists, or it lacks `range_end_commit`, you must pass `--start-commit`
- `--start-commit` must resolve through `git rev-parse --verify`
- if the resolved range contains no new commits, stop with an error and do not write the report file

## Writing Rules

Write `docs/daily-report/YYYY-MM-DD.md`.

Rules:
- Title: `# YYYY-MM-DD 工作日报`
- Write the YAML front matter before the title
- Write 3 to 6 themed blocks
- Keep the tone close to the previous plain-language style: direct, concrete, low abstraction
- Do not mention commit hashes in the body
- Do not use absolute filesystem paths
- Prefer repo-local relative paths such as `tests/test_openpi_runtime_bridge.py`, `tinker_server/openpi/routes.py`, `src/mint/openpi/client.py`, `src/openpi/integration/runtime.py`
- Route and API names are allowed
- Mention failures when verification exposed them
- Do not create `具体变更：`、`证据：`、`验证：`、`剩余问题：` labels
- Do not use per-theme markdown headings such as `## ...`

Each theme block should contain:
- 1 opening sentence that starts with a concise summary clause and `：`, then immediately enters the concrete change
- 1 sentence or short paragraph naming the remaining gap
- exactly one screenshot placeholder block carrying the verification command and result
- between adjacent theme blocks, insert two blank lines, then `---`, then two blank lines

Bad:
- “推进主线并进一步收紧边界。”

Good:
- “远端 smoke 入口继续收紧：`tests/test_openpi_remote_deployment_smoke.py` 现在把远端 status、artifact 和 inference smoke 收进 env-driven 路径。真实 checkpoint lane 还没有进入默认门禁。[测试截图占位：远端 smoke；运行：cd src/mint && .venv/bin/pytest tests/test_openpi_remote_deployment_smoke.py -vv -ra；结果：22 passed, 3 skipped in 0.41s]”

## Failure Handling

Failures belong in the report when verification exposed them.

Write failures as:
- what was verified
- what symptom appeared
- what capability this blocks or weakens

Do not hide failures behind vague language such as “还需要继续打磨”。

## Screenshot Placeholders

Do not capture screenshots automatically.

Append one placeholder block after each theme:
- `[测试截图占位：<验证目的>；运行：<命令>；结果：<结果>]`
- `[失败截图占位：<验证目的>；运行：<命令>；现象：<一句话现象>]`

If no command could be selected:
- `[测试截图占位：未自动定位到命令；需人工补充]`

Keep commands inside the placeholder only. Do not repeat them in prose.

## Quality Filter

Before saving the file, check:
- filename matches `YYYY-MM-DD`
- front matter contains the commit range and human-readable author dates
- prose contains no code blocks
- prose uses no per-theme `##` headings
- adjacent theme blocks are separated by `---` with blank lines around it
- every theme contains at least one relative path, test name, or route/API name
- no theme body mentions a commit hash
- no theme contains `具体变更：`、`证据：`、`验证：`、`剩余问题：`
- every verification claim is backed by a fresh command result
- every failure statement names the symptom and impacted capability

## Collector Notes

`scripts/collect_daily_report_facts.py` already enforces these boundaries:
- resolves the report range from the previous daily report or `--start-commit`
- emits `code_evidence` from changed files, changed tests, and submodule gitlink ranges
- excludes deleted progress-doc paths and `README.md` directory guides
- preserves progress docs as explanatory context after code evidence
- treats plan docs as verification-command sources
- only keeps selected current-state subtarget sentences from `docs/targets/`
- errors when the resolved range contains no new commits

If the collector output looks wrong, fix the collector or its tests first. Do not paper over bad facts in prose.
