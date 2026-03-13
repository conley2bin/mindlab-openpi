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

## Canonical Layout

- 顶层只保留当前生效的 canonical plan 文件。
- 每个仍然活跃的 `ST-xx` 在顶层最多保留一份 canonical plan。
- 以日期命名的专题设计、实验草稿、一次性执行清单，不应继续留在顶层。
- 如果这些临时材料里的结论被接受，就把有效结论吸收到对应 `st-xx-*.md`，然后直接删除原文件。

## Suggested Naming

- `st-01-*.md`
- `st-02-*.md`
- `st-03-*.md`
- `st-04-*.md`
- `st-05-*.md`
- `st-06-*.md`
- `st-07-*.md`
- `st-08-*.md`
- `st-09-*.md`
- `st-10-*.md`

这些文件名分别对应 `docs/targets/subtarget-xx-*.md` 中相同编号的子目标。

## Rules

- 这里可以写到任务层和落地顺序，但不要把每日状态记录混进来。
- 已发生的进展、阻塞、偏差和结论，应回写到 `docs/progress/` 或 `docs/daily-report/`。
- 如果一个方案已经失效，不要在原文里写成长篇变更历史；应直接更新当前方案，必要时在 `progress/` 记录变化原因。
- 如果某个专题设计已经被吸收进 canonical plan，就删除原始 dated doc，不要在仓库里同时保留两份“当前方案”。
