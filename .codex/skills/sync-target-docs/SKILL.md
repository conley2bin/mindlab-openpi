---
name: sync-target-docs
description: Use when updating docs/targets/target.md or any docs/targets/subtarget-*.md file, especially after changing subtarget status, adding or removing a subtarget, or checking whether the target table drifted from subtarget documents.
---

# Sync Target Docs

## Overview

Keep `docs/targets/target.md` and `docs/targets/subtarget-*.md` structurally consistent.

This skill only checks and synchronizes document structure. It does not invent goals, rewrite target正文, make planning decisions, or touch `docs/plans/`, `docs/progress/`, or `docs/daily-report/`.

## Invariants

- `docs/targets/target.md` contains one row per subtarget in `## 子目标总表`
- each table row points to exactly one `subtarget-*.md`
- each subtarget file has a top-level `# ST-XX ...` heading
- each subtarget file has a `## Current Status` section
- each subtarget file contains a `- Status: ...` line under `## Current Status`
- the `Status` column in `target.md` matches the status declared in the subtarget file
- orphan `subtarget-*.md` files are errors

Allowed statuses:

- `backlog`
- `blocked`
- `completed`
- `drafted`
- `dropped`
- `in_progress`
- `research`
- `todo`

## Workflow

1. Edit the relevant `docs/targets/subtarget-*.md` file first.
2. Check structural correspondence manually:

```bash
find docs/targets -maxdepth 1 -type f | sort
rg -n "^## 子目标总表|^\\| ST-|^## Current Status|^- Status:" docs/targets/target.md docs/targets/subtarget-*.md
```

3. If the only drift is the `Status` value in `target.md`, update the table manually to match the subtarget file.
4. Re-run the checks.
5. Inspect the diff manually.

## What To Check

- every `ST-XX` row in `target.md` has one matching `subtarget-xx-*.md` file
- the numeric suffix in `ST-XX` matches the numeric suffix in `subtarget-xx-*.md`
- every `subtarget-xx-*.md` file is represented in `target.md`
- each linked filename in `target.md` matches the actual file path
- `Status` values match exactly
- each `Status` value is one of the allowed statuses listed in this skill
- no extra or missing subtargets exist after renames, splits, or deletions

## Boundaries

- this skill only enforces structural consistency inside `docs/targets/`
- it does not create new goals or subtargets
- it does not rename subtargets automatically
- it does not rewrite dependencies, focus descriptions, or正文内容
- it does not modify `docs/plans/`, `docs/progress/`, or `docs/daily-report/`

If IDs, filenames, links, or file presence are wrong, fix the documents manually first.
