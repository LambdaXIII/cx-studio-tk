# Changelog

## 0.1.1

基于 jpegger 迁移审计反馈的修正：

### 架构改进

- **主题透明机制**（N2）：`WealthyDocument` / `WealthyHelp` 不再持有主题（移除 `theme` / `styles` / `DEFAULT_STYLES` 属性）。渲染时通过 `__rich_console__` **兜底补全**调用方未定义的 `cx.*` 样式——不覆盖调用方已有定义，仅在缺失时用 `default_theme` 填充。第三方不应用 `default_theme` 时组件仍可渲染（透明兼容）。
- **ActionGroup 特化**（B2）：新增 `cx_wealthy.help.action_group.ActionGroup`，在 help 特化层继承 `Group` 提供 `add_action` 便利方法。`WealthyHelp.add_group` 覆盖父类方法返回 `ActionGroup`。`Group`（document 通用核心）保持语义纯净，不感知 `Action` / flags / nargs。
- **接口级样式统一**（B1）：`cx_tools/app/iappenv.py` 的 11 个 `DEFAULT_STYLES` 迁移到 `cx_wealthy/theme.py` 的 `BASE_STYLES`。主题来源单一化，cx_wealthy 作为依赖统一提供所有 `cx.*` 样式。

### Bug 修复

- **detail markup 解析**（N1）：`WealthDetailTable` 的 KEY 和 VALUE 渲染均改用 `Text.from_markup(str(...))`，与 `console.print(str)` 默认解析 markup 的行为对齐。原 `Text(str(...))` 不解析 markup，导致 `[cyan]#0 AutoResize[/]` 等显示为字面量。
- **Action flag 校验**（B3）：`_validate_flags` 分两类校验——选项（`^[prefix_chars]+\w[\w-]*$`）和位置参数名（`^\w[\w-]*$`），支持位置参数名和含连字符的 flag（如 `--force-overwrite`）。

## 0.1.0

- 初始发布，建立 `cx-wealthy` 包骨架。
- 主要模块（按实现计划）：
  - `theme` — `cx.*` 命名空间主题预设（success / error / warning / info 等）。
  - `rich_types` — 对外便利的 Rich 高频类型出口。
  - `label` — 紧凑标签协议 `RichLabelMixin` 与 `RichLabel` 包装器。
  - `detail` — 详情键值面板协议 `RichDetailMixin` 与 `WealthDetailPanel` / `WealthDetailTable`。
  - `document` — 通用结构化文档核心：`Node` / `Group` / `Note` / `WealthyDocument`。
  - `help` — 帮助系统特化层：`Action` / `WealthyHelp`。
  - `indexed_list` — 带索引列表面板 `IndexedListPanel`。
  - `columns` — 最大列数布局 `MaxColumnsLayout`。
  - `tutorial` — 本地化教程渲染 `render_tutorial()`。
