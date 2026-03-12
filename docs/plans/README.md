# Plans Directory Guide

## Purpose

`docs/plans/` 存放实施方案文档。

这里的文档回答的是：

- 某个目标或子目标准备如何落地
- 需要先后冻结哪些决策
- 预期涉及哪些仓库、目录、接口与验证面
- 如何把目标文档中的边界变成可执行方案

## Expected Relationship With Targets

- 每份实施方案都应明确映射到一个 `ST-xx` 子目标，或明确说明它横跨哪些 `ST-xx`。
- `docs/targets/` 是上位约束，`docs/plans/` 不应违背其中的边界和非目标。
- 如果实施方案发现目标文档有遗漏，应先回补 `docs/targets/`，再继续写方案。

## Suggested Naming

- `st-01-*.md`
- `st-02-*.md`
- `st-03-*.md`
- `st-04-*.md`
- `st-05-*.md`
- `st-06-*.md`
- `st-07-*.md`
- `st-08-*.md`

这些文件名分别对应：

- `ST-01` / `docs/targets/subtarget-01-*.md`
- `ST-02` / `docs/targets/subtarget-02-*.md`
- `ST-03` / `docs/targets/subtarget-03-*.md`
- `ST-04` / `docs/targets/subtarget-04-*.md`
- `ST-05` / `docs/targets/subtarget-05-*.md`
- `ST-06` / `docs/targets/subtarget-06-*.md`
- `ST-07` / `docs/targets/subtarget-07-*.md`
- `ST-08` / `docs/targets/subtarget-08-*.md`

## Rules

- 这里可以写到任务层和落地顺序，但不要把每日状态记录混进来。
- 已发生的进展、阻塞、偏差和结论，应回写到 `docs/progress/` 或 `docs/daily-report/`。
- 如果一个方案已经失效，不要在原文里写成长篇变更历史；应直接更新当前方案，必要时在 `progress/` 记录变化原因。
