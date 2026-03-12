# Targets Directory Guide

## Purpose

`docs/targets/` 存放 OpenPI 接入 Mint 这条主线的长期目标文档。

这里的文档回答的是：

- 总体目标是什么
- 为什么这样分仓和分层
- 哪些边界不能被后续实现破坏
- 每个子目标在什么条件下才算可以继续往下推进

## File Roles

- `target.md`: 主线总目标，描述整体目标、范围、长期约束、仓库职责与子目标依赖关系。
- `subtarget-xx-*.md`: 对应单个子目标，描述该子目标的目标、边界、语义冲突、非目标、依赖和 readiness gates。

## Naming Mapping

- `subtarget-01-*.md` 对应 `ST-01`
- `subtarget-02-*.md` 对应 `ST-02`
- `subtarget-03-*.md` 对应 `ST-03`
- `subtarget-04-*.md` 对应 `ST-04`
- `subtarget-05-*.md` 对应 `ST-05`
- `subtarget-06-*.md` 对应 `ST-06`
- `subtarget-07-*.md` 对应 `ST-07`
- `subtarget-08-*.md` 对应 `ST-08`

`subtarget-xx` 是目标文档文件名前缀，`ST-xx` 是在目标表、方案文档、进度文档里引用同一子目标时使用的短标识。

## Rules

- `target.md` 保持长期视角，不写具体文件级任务。
- `subtarget-xx` 可以比 `target.md` 更具体，但仍然是目标/约束文档，不是实施计划。
- 任何阶段性任务拆解、文件修改顺序、验证命令、里程碑安排，应写入 `docs/plans/`，不应继续堆进 `docs/targets/`。
- 进度变化和已完成事项不写在这里，写到 `docs/progress/` 或 `docs/daily-report/`。
