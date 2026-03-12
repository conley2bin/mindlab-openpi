---
name: mint-prod
description: Use when working from the repo root on the Mint production environment, including prod-safe read operations, production checks, or deciding how a task should run against mint-prod-volcano instead of development.
---

# Mint Prod

Use the owning Mint skill:

- `src/mint/.claude/skills/mint-prod/SKILL.md`

Rules:

- Treat this root skill as a trigger and routing shim only.
- Read the Mint owning skill before running production commands.
- For cluster lifecycle actions such as creating or tearing down Volcano tasks, also use `volcano-cluster`.
- Do not copy production SOPs, queue rules, or safety procedures into this wrapper.
