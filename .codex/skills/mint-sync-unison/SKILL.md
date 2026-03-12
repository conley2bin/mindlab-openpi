---
name: mint-sync-unison
description: Use when verifying or operating local-to-PFS code sync for Mint dev work, especially when `mint-dev` sees stale code, `/root/tinker_project/tinker-server` is a symlink into PFS, or you need to confirm the per-user Unison profile and daemon are active.
---

# Mint Sync Unison

## Overview

Mint dev sync is driven from the local machine. `mint-dev` consumes the synced PFS tree through a symlink; it is not the authoritative side of the sync.

Use this skill when code on `mint-dev` looks stale or when you need to verify that your local `src/mint` tree is the one being mirrored into PFS.

## Canonical Paths

- Local source root: your local `src/mint`
- Remote PFS root: resolve with `readlink -f /root/tinker_project/tinker-server`
- Remote server path: `/root/tinker_project/tinker-server`

`ssh mint-dev` lands as `root`, so remote `$USER` is not the PFS owner. Derive the actual PFS path from the symlink target. Remote `.git` absence is expected. The Unison profile ignores `.git`.

## Local Checks

```bash
systemctl --user show "unison@volcano-tinker-$USER.service" \
  -p Id -p LoadState -p ActiveState -p SubState -p UnitFileState
pgrep -af "unison.*volcano-tinker-$USER"
sed -n '1,120p' ~/.unison/volcano-tinker-$USER.prf
tail -n 50 ~/.unison/unison.log 2>/dev/null || true
```

Healthy signals:

- unit exists and is `active`
- process command includes `volcano-tinker-$USER`
- profile points to your local `src/mint`
- remote root matches the path declared in your Unison profile and the current symlink target from `/root/tinker_project/tinker-server`

## Remote Checks

```bash
ssh mint-dev 'readlink -f /root/tinker_project/tinker-server'
ssh mint-dev 'PFS_ROOT=$(readlink -f /root/tinker_project/tinker-server); ls -ld "$PFS_ROOT" 2>/dev/null || true'
ssh mint-dev 'PFS_ROOT=$(readlink -f /root/tinker_project/tinker-server); ls -ld "$PFS_ROOT/.git" 2>/dev/null || echo no_remote_git_dir'
```

## Profile Template

Use `references/volcano-tinker.prf` as the root template. Replace:

- local root path
- `__PFS_USER__`

The template is intentionally scoped to `src/mint`, not the whole monorepo.

## Guardrails

- Do not run one-off syncs and assume the daemon is healthy.
- Do not sync to shared `/vePFS-Mindverse/share/code/tinker-server`.
- Do not treat remote `.git` absence as a sync failure.
- Do not debug stale code on `mint-dev` before checking the local daemon state.
