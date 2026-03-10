---
name: write-daily-report
description: Use when writing a daily work report from repository evidence, especially when the report must be based only on same-day committed changes plus same-day updates in workspace/docs/targets or workspace/docs/plans, and when both a professional report and a plain-language companion report are required.
---

# Write Daily Report

## Overview

Use this skill to write two daily reports from committed repository facts:
- `workspace/docs/日报/YYYY-MM-DD.md`
- `workspace/docs/日报/YYYY-MM-DD-通俗版.md`

The collector script defines the fact boundary. The model only groups facts into themes, runs the smallest relevant verification commands, and writes the two reports.

## Workflow

1. Determine the target date.
   - Default to today.
   - Use `YYYY-MM-DD`.

2. Collect facts.

```bash
python3 .codex/skills/write-daily-report/scripts/collect_daily_report_facts.py \
  --date 2026-03-10 \
  --repo-root /absolute/path/to/repo \
  --json-indent 2
```

3. Read the JSON output and treat it as the only fact source for prose.
   - `commits`: same-day commits by author date
   - `progress_docs`: same-day committed updates under `workspace/docs/targets/` and `workspace/docs/plans/`
   - `facts`: prose-ready facts from target docs plus commit subjects
   - `verification_commands`: candidate commands extracted from plan docs and target docs

4. Build 2 to 4 work themes.
   - Group by work intent, not by repository name.
   - Merge facts that describe one capability chain.
   - Prefer target-doc facts over raw commit subjects when both say the same thing.

5. Select the smallest relevant verification commands.
   - Run 1 to 2 commands per theme when possible.
   - Prefer commands that directly test the capability described by that theme.
   - Do not run full test suites unless the collector found no narrower command.

6. Write both markdown files in `workspace/docs/日报/`.

## Fact Boundary

Use only:
- same-day committed changes
- same-day committed updates in `workspace/docs/targets/`
- same-day committed updates in `workspace/docs/plans/`
- fresh output from the selected verification commands

Do not use:
- uncommitted working-tree changes
- memory of previous conversations
- unstated intent
- manual guesses about why something happened

Plan docs are command sources, not prose fact sources. Use them to find verification commands. Do not turn design alternatives or task lists into report sentences.

## Writing Rules

### Professional Report

Write `workspace/docs/日报/YYYY-MM-DD.md`.

Rules:
- Title: `# YYYY-MM-DD 工作日报`
- Write 2 to 4 themed sections
- Each section covers one work theme
- Write at capability level, not implementation detail
- Keep terms professional, but expand vague labels into concrete capability changes
- Mention failures when verification exposed them

Each theme section should contain:
- what capability changed today
- what state it reached
- what verification passed or failed
- what concrete issue remains, if any

Do not put code snippets, file paths, script paths, or API names into prose.

### Plain-Language Report

Write `workspace/docs/日报/YYYY-MM-DD-通俗版.md`.

Rules:
- Title: `# YYYY-MM-DD 工作日报（通俗版）`
- Keep the same theme count and theme order as the professional report
- Explain what problem each theme is solving in direct language
- Keep the same facts and verification results
- Lower the abstraction level, but do not add new claims

## Failure Handling

Failures belong in the report when verification exposed them.

Write failures as:
- what was verified
- what symptom appeared
- what capability this blocks or weakens

Do not hide failures behind vague language such as “still needs polish”.

## Screenshot Placeholders

Do not capture screenshots automatically.

Append one placeholder block after each theme:
- `[测试截图占位：<验证目的>；运行：<命令>；结果：通过]`
- `[失败截图占位：<验证目的>；运行：<命令>；现象：<一句话现象>]`

If no command could be selected:
- `[测试截图占位：未自动定位到命令；需人工补充]`

Keep commands inside the placeholder only. Do not repeat them in prose.

## Quality Filter

Before saving the files, check:
- both filenames match `YYYY-MM-DD` and `YYYY-MM-DD-通俗版`
- both reports use the same theme order
- prose contains no code blocks
- prose contains no file paths, script paths, or API names
- every verification claim is backed by a fresh command result
- every failure statement names the symptom and impacted capability

## Collector Notes

`scripts/collect_daily_report_facts.py` already enforces these boundaries:
- filters commits by author date
- excludes deleted progress-doc paths
- treats plan docs as verification-command sources
- keeps target-doc state sentences and drops static guidance lines

If the collector output looks wrong, fix the collector or its tests first. Do not paper over bad facts in prose.
