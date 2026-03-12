---
name: ray-namespace-isolation
description: Use when running Mint against shared dev Ray clusters, especially when choosing `TINKER_RAY_NAMESPACE`, `MINT_RAY_NAMESPACE`, `PFS_TINKER_PATH`, or checking whether actors, futures, and worker imports are isolated per developer or per issue.
---

# Ray Namespace Isolation

## Overview

Dev cluster isolation is a three-part contract:

- code root: `PFS_TINKER_PATH`
- actor namespace: `TINKER_RAY_NAMESPACE`
- detached-store namespace: `MINT_RAY_NAMESPACE`

If any one of these points at another developer or a shared default, isolation is broken.

## Required Rules

- `MINT_RAY_NAMESPACE` must equal `TINKER_RAY_NAMESPACE`.
- `PFS_TINKER_PATH` must point at your per-user or per-issue PFS tree.
- Do not create, inspect, or kill actors outside the active namespace unless the task explicitly requires cross-namespace work.
- Do not submit workers that import shared `/vePFS-Mindverse/share/code/tinker-server`.

## Recommended Naming

Per-user:

```bash
export TINKER_RAY_NAMESPACE="tinker_$USER"
export MINT_RAY_NAMESPACE="$TINKER_RAY_NAMESPACE"
export PFS_TINKER_PATH="/vePFS-Mindverse/share/code/$USER/tinker-server"
```

Per-issue:

```bash
export ISSUE=123
export TINKER_RAY_NAMESPACE="tinker_${USER}_issue_${ISSUE}"
export MINT_RAY_NAMESPACE="$TINKER_RAY_NAMESPACE"
export PFS_TINKER_PATH="/vePFS-Mindverse/share/code/$USER/tinker-server-issue-$ISSUE"
```

## Verification

Before starting a server or submitting workers, print the tuple you will use:

```bash
printf '%s\n' \
  "TINKER_RAY_NAMESPACE=$TINKER_RAY_NAMESPACE" \
  "MINT_RAY_NAMESPACE=$MINT_RAY_NAMESPACE" \
  "PFS_TINKER_PATH=$PFS_TINKER_PATH"
```

Remote server path check:

```bash
ssh mint-dev 'readlink -f /root/tinker_project/tinker-server'
```

If the resolved path does not match `PFS_TINKER_PATH`, fix the symlink or worker template before proceeding.

## Guardrails

- Do not reuse another developer's namespace.
- Do not let the server use one namespace while stores use another.
- Do not trust old Ray actors after changing namespace or PFS path.
- Treat any worker template with shared code root as invalid for new submissions.
