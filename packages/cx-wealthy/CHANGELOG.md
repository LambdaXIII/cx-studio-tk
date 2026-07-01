# Changelog

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
