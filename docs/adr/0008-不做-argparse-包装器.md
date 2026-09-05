# 不做 argparse 包装器

> 领域：cx-wealthy · 适用范围：cx-wealthy

`WealthyHelp` 不提供 `from_argparse(parser)` 适配器。argparse 的扁平字段信息不足以驱动声明式排版，且生态中已有大量 argparse 美化器。本包的价值在于独立于任何解析器的声明式排版能力。

## Considered Options

- **提供 `from_argparse(parser)` 适配器**：argparse 的扁平字段不足以驱动声明式排版，包装产出的排版无法达到独立构建的灵活度；生态有成熟 argparse 美化器，不应在此重复。

## Consequences

- `WealthyHelp` 保持解析器无关，声明式排版能力独立于任何参数解析方案。
