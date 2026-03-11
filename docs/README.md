# Docs Directory Guide

## Purpose

`docs/` 用于存放项目级文档，但不同类型的文档必须分层存放，避免把长期目标、实施方案、进度记录和日报混写到同一处。

## Directory Roles

- `docs/targets/`: 长期目标、子目标、边界、约束与 readiness gates。
- `docs/plans/`: 与目标一一对应的实施方案文档，回答如何落地。
- `docs/progress/`: 阶段进展、状态变化、阻塞项和已发生事实。
- `docs/daily-report/`: 按日期记录的工作日志和当日观察。

## Rules

- 目标文档写 `what / why / boundaries`，不写逐步任务清单。
- 实施方案文档写 `how`，但不承担每日状态记录职能。
- 进度文档记录事实，不替代目标或方案。
- 日报只保留时间序列信息，不作为长期架构真相来源。
- 如果一份文档需要长期维护并指导后续开发，优先判断它应该进入 `targets/` 还是 `plans/`，而不是塞进 `progress/`。
