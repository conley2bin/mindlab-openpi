---
name: sync-target-docs
description: Use when updating workspace/docs/targets/target.md or any subtarget-*.md file, especially after changing status, adding or removing a subtarget, or checking whether target progress tracking drifted from subtarget documents.
---

# Sync Target Docs

## Overview

Keep `workspace/docs/targets/target.md` and `workspace/docs/targets/subtarget-*.md` structurally consistent.

This skill enforces correspondence. It does not invent goals, rewrite正文, or make semantic planning decisions.

## Invariants

- `target.md` contains one row per subtarget in `## 子目标总表`
- each row points to exactly one `subtarget-*.md`
- each subtarget has a top-level `# ST-XX ...` heading
- each subtarget has a `## 当前状态` section
- the table status column matches the subtarget status
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

1. Edit the relevant `subtarget-*.md` first.
2. Run:

```bash
python3 workspace/scripts/sync_target_docs.py check --target workspace/docs/targets/target.md
```

3. If the only drift is the status column, run:

```bash
python3 workspace/scripts/sync_target_docs.py sync-status --target workspace/docs/targets/target.md
```

4. Run `check` again.
5. Inspect the diff manually.

## Boundaries

- `sync-status` only updates the `状态` column in `target.md`
- it does not create new rows
- it does not rename subtargets
- it does not rewrite dependencies
- it does not modify subtarget正文

If IDs, links, or file presence are wrong, fix the documents manually first.
