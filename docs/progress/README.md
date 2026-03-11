# Progress Directory Guide

## Purpose

`docs/progress/` 存放阶段进展文档。

这里的文档回答的是：

- 哪些目标或方案已经推进到什么状态
- 哪些问题已经暴露
- 哪些阻塞、风险、偏差需要被跟踪
- 哪些结论已经被实施工作验证

## File Roles

- `openpi-integration-baseline.md`: 记录当前代码现实、当前缺口和主线起点，不写未来愿景。
- `openpi-contract-glossary.md`: 记录跨仓统一术语和命名边界，避免后续文档和实现各自发明概念。
- `openpi-compatibility-matrix.md`: 记录当前支持面、契约 owner、验证锚点和未开始项。
- `openpi-validation-baseline.md`: 记录当前 hard gates、弱验证路径、缺失验证层和归因口径。

## Rules

- 这里记录已经发生的事实和当前状态，不承担长期目标定义职能。
- 不要把新的架构边界直接先写进 `progress/`；如果是长期约束，应先更新 `docs/targets/`。
- 不要把未来落地方案长期存放在这里；如果是实施设计，应写进 `docs/plans/`。
- 进度文档可以引用 `ST-xx` 和对应方案文档，但不应替代它们。
