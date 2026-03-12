---
name: volcano-cluster
description: Use when working from the repo root on Volcano ML platform tasks such as creating or tearing down Ray clusters, allocating GPUs, listing or canceling Volcano tasks, checking Ray dashboard access, or cleaning up stale cluster state for Mint.
---

# Volcano Cluster

Use the owning Mint skill:

- `src/mint/.claude/skills/volcano-cluster/SKILL.md`

Rules:

- Treat this root skill as a trigger and routing shim only.
- Read the Mint owning skill before taking any Volcano or Ray cluster action.
- Do not duplicate queue IDs, YAML snippets, SSH hosts, or CLI procedures here. The Mint skill is the single source of truth.
- If the task is environment-specific server work after cluster lifecycle is settled, also consult `mint-dev` or `mint-prod`.
