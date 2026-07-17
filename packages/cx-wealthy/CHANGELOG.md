# Changelog

## 0.9.0

### 版本统一

- 本次与其余包同步发布，统一版本号为 0.9.0

### 展示字段重命名与语义统一

- **`descriptor` → `detailer` 全量重命名**：统一「渲染器」命名（`titler` / `detailer` 对称），覆盖
  `Node`、`Group`、`Action`、`HelpGroup` 四个类的属性名、方法名（`_default_descriptor` → `_default_detailer`）、
  kwargs key（`"descriptor"` → `"detailer"`）及所有 docstring 引用。
- **公共 API 参数 `description=` → `detail=`**：`add_group` / `add_command` / `add_action` 的
  描述参数从 `description=` 统一改为 `detail=`，与 `Node.detail` 语义字段同名，消除「对外叫 description、
  内部叫 detail」的双轨命名。
- **`add_note` 透传支持**：`Group.add_note` / `WealthyDocument.add_note` 增加 `**kwargs`
  参数，支持透传 `titler` / `detailer`，与 `add_group` 等接口对齐。
- **Node 类 docstring 重写**：完整说明 `name`/`detail`（语义字段）、`titler`/`detailer`（渲染器）、
  `title`/`description`（计算属性）六者关系，以及 `title`/`description` 的三条计算路径（显式 None / 非 callable 回退 /
  callable 替代）。

### 调用方迁移

- **hosts_keeper `app_help.py`**：16 处 `description=` → `detail=`
- **jpegger `simple_appcontext.py`**：13 处 `description=` → `detail=`（argparse 的 `description=`
  保留不变）

### 禁止范围

- `media_killer`、`media_scout`、`ffpretty`、`cx_wealth`（旧包）均未触碰，仍使用旧版接口。

## 0.3.0

### 架构重构

- **HelpGroup 单类取代 ActionGroup + CommandGroup**：能力重复的两个类合并为单一 `HelpGroup(Group)`，通过 `commands` 字段区分参数分组语义（`commands=()`）与命令语义（`commands=("list",)`）。
  - 删除 `ActionGroup` 与 `CommandGroup` 类、`command_group.py`、`action_group.py` 文件
  - 删除 `add_command_group()` 方法（分组用 `add_group()`）
  - 删除 `is_nested` 属性（死代码）
  - 新增 `HelpGroup.iter_commands()` 递归遍历辅助方法
  - 渲染层 `isinstance(x, CommandGroup)` → `isinstance(x, HelpGroup) and x.is_command`
  - **所有现有 CLI 工具的 --help 输出字面不变**
- **导出更新**：`ActionGroup`、`CommandGroup` 从 `cx_wealthy` / `cx_wealthy.help` 导出中删除，新增 `HelpGroup`

### 修复

- **恢复文档导入**：`cx_wealthy/__init__.py` 中补回误删的 `from .document import Group, Node, Note, WealthyDocument`——`__all__` 中仍列出这些符号但导入被意外移除。
- **恢复 epilog 样式**：`theme.py` 中补回误删的 `cx.help.epilog` 样式，epilog 文本不再回退到默认 Rich 样式。
- **usage 渲染修复**（三个渲染 bug）：
  - 修复子命令详版行与首行不对齐：将混合的 Table+Padding 结构统一为双列 Table，prog 末尾空格作列间分隔，所有行在同一右列中自然对齐。
  - 修复 usage 与 description 左 padding 不一致：Table 统一加 `Padding(pad=(0,0,0,2))`。
  - 修复子命令 pipe 排在参数后面：简版行拼接顺序从 `path → actions → sub_commands` 改为 `path → sub_commands → actions`，符合 CLI 惯例。
- **列间距职责上移**：前导空格从 `_render_node_usage` 的简版行内部提取到 Table 层（prog 末尾空格），不再由数据层隐含提供。

## 0.2.0

### 新特性

- **CommandGroup 机制**：`WealthyHelp` 新增 `CommandGroup` 类型，原生支持子命令结构（git/docker 风格 CLI）。
  - `CommandGroup` 继承 `ActionGroup`，兼具命令本身与组织容器两种角色
  - `add_command(*keywords, name=, description=)` / `add_command_group(name=, description=)` API
  - 递归 usage 渲染：简版总览行 + 每个子命令详版行，支持嵌套
  - details 渲染：CommandGroup 作为子命令区块，递归展开
  - 无 CommandGroup 的工具（如 jpegger）行为完全不变
- **新增样式**：`cx.help.usage.command`（命令关键词样式）
- **新增导出**：`CommandGroup` 在 `cx_wealthy` 和 `cx_wealthy.help` 顶层导出

### 文档

- 新增 `docs/wealthy-help-guide.md`：WealthyHelp 完整用法文档
- README 简要介绍补充 CommandGroup 示例

## 0.1.2

修正 0.1.1 引入的问题：

- **detail str 语义**：`_check_value` 和 `_make_table_from_rows` 不再用 `Text.from_markup` 解析 `str` 类型 key/value。`str` = 数据（逐字显示），`Text` = 富文本（保留样式）。避免用户数据中匹配 Rich 样式名的 `[...]` 被当作样式标签消费。
- **移除私有 API**：`WealthyDocument.__rich_console__` 不再访问 `console._theme_stack`（Rich 私有属性），不再做主题兜底补全。组件完全主题透明——调用方通过 `Console(theme=default_theme)` 提供样式。
- **BASE_STYLES 值恢复**：`cx.info`/`cx.success`/`cx.error`/`cx.warning`/`cx.number` 恢复为 0.1.0 的设计值（bold 变体、cyan 色调），不再从 iappenv 复制。

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
