---
name: mint-dev
description: Use when working from the repo root on the Mint development environment, including dev server checks, dev-specific operational commands, or deciding how a task should run against mint-dev instead of production.
---

# Mint Dev

Use the owning Mint skill:

- `src/mint/.claude/skills/mint-dev/SKILL.md`

Rules:

- Treat this root skill as a trigger and routing shim only.
- Read the Mint owning skill before running dev environment commands.
- For cluster lifecycle actions such as creating or tearing down Volcano tasks, also use `volcano-cluster`.
- Do not copy environment variables, SSH instructions, or operational SOPs into this wrapper.
