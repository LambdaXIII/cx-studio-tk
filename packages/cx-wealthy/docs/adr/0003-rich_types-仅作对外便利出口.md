# rich_types 仅作对外便利出口

`rich_types` 模块是给使用方的 `r` 别名出口（与项目 `r` 约定一致），收窄到高频类型。决定：库内部一律用真实 import 路径（`from rich.table import Table`），`rich_types` 只服务使用方。

## Considered Options

- **内部也用 `rich_types` 别名**：内部用别名会损失 IDE 跳转精度、类型推断绕一道、grep 无法区分真实类型与别名。

## Consequences

- 新增 Rich 类型时内部直接 import 零成本，不需要同步注册到 `rich_types`。
- 使用方仍可经由 `rich_types` 获得稳定、收窄的便利出口；导出边界可控。
