# cx-wealthy Specification

## Purpose
定义 cx-wealthy（Rich 终端结构化文档与 UI 组件库）的现行行为契约：通用复合树与帮助系统双层分层架构、`__rich_label__` / `__rich_detail__` 双渲染协议及其 mixin+包装器双轨承载、`__rich_console__` yield 范式、`rich_types` 对外便利出口语义、最小依赖链与主题透明性约束、公开导出约定与私有命名规则。

## Requirements

### Requirement: 文档分层：通用核心与帮助特化双层分离

cx-wealthy 的文档系统 MUST 由两层构成：`document/` 通用复合树核心（`Node` 基类、`Group` 分组节点、`Note` 注释节点、`WealthyDocument` 根节点）和 `help/` 帮助特化层（`Action` 帮助条目、`HelpGroup` 帮助分组/子命令、`WealthyHelp` 帮助文档根节点）。通用核心 MUST NOT 引用任何帮助特化语义（如 flags、nargs、usage）。`WealthyHelp` MUST 继承 `WealthyDocument`，`HelpGroup` MUST 继承 `Group`，`Action` MUST 继承 `Node`。通用核心的能力（"分组 + 条目 + 注释"的结构化输出）MUST NOT 被封装在帮助层内部。

#### Scenario: 通用核心独立于帮助语义

- **WHEN** 查阅 `document/` 模块的源码
- **THEN** 其中不出现 flags、nargs、usage 等帮助特化概念的引用或导入

#### Scenario: 帮助层继承通用核心

- **WHEN** `WealthyHelp` 渲染文档
- **THEN** 其 render 流程通过继承的 `WealthyDocument` 机制 yield 各部分（usage、details、epilog），复用通用复合树的节点管理能力

#### Scenario: 非帮助类结构化文档基于通用核心构建

- **WHEN** 使用方需要输出"分组 + 条目 + 注释"结构（不限于帮助）
- **THEN** 可直接实例化 `WealthyDocument` 及其节点类型构建，无需经过帮助层

### Requirement: `__rich_label__` 紧凑标签协议

`__rich_label__` 是可选的紧凑标签渲染协议。实现该协议的类型 MUST yield 一组 Renderable 片段，渲染时由拼接逻辑用分隔符组装为单行 `Text`，用于列表行标题、行内摘要等紧凑场景。`RichLabelMixin` 提供默认 `__rich__` 实现（调用 `__rich_label__` 并组装为 `Text`），`RichLabel` 是不依赖继承的包装器，两者共享同一套渲染逻辑（`_render_label`）。

#### Scenario: Mixin 提供默认 `__rich__`

- **WHEN** 使用方继承 `RichLabelMixin` 并实现 `__rich_label__` yield 标签片段
- **THEN** `console.print(obj)` 直接输出由片段拼接的 `Text`，无需显式包装

#### Scenario: 包装器渲染与 Mixin 一致

- **WHEN** 使用方不继承 `RichLabelMixin`，改用 `RichLabel(obj)` 包装
- **THEN** 渲染结果与直接打印 mixin 实例一致（同一套 `_render_label` 逻辑）

#### Scenario: detail 中的 `__rich_label__` 自动识别

- **WHEN** `__rich_detail__` yield 的 value 实现了 `__rich_label__`
- **THEN** 该 value 自动以标签形态渲染（经 `RichLabel` 包装后作为行内容显示）

### Requirement: `__rich_detail__` 键值面板协议

`__rich_detail__` 是可选的键值面板渲染协议。协议约定：yield `(key, value)` 或 `(key, value, default)` 三元组。三元组中 `value == default` 时该行 MUST NOT 显示（去重）。`RichDetailMixin` 提供默认 `__rich__` 实现，将对象包装为 `WealthyDetailPanel`。`WealthyDetailPanel`（Panel 形态）和 `WealthyDetailTable`（Table 形态）是共享同一套渲染逻辑的包装器。key/value 的类型语义：`str` 类型 MUST 逐字显示不解析 markup（数据安全）；`Text` 类型 MUST 保留已有样式。

#### Scenario: 三元组去重

- **WHEN** `__rich_detail__` yield 三元组 `(key, value, default)` 且 `value == default`
- **THEN** 该行不出现在最终渲染结果中

#### Scenario: 嵌套渲染——sub-panel

- **WHEN** `__rich_detail__` yield 的 value 自身实现了 `__rich_detail__` 或 `__rich_repr__`
- **THEN** 该 value 自动渲染为嵌套的 sub-panel（`WealthyDetailPanel`），而非退化为字符串

#### Scenario: 列表值自动渲染

- **WHEN** `__rich_detail__` yield 的 value 为列表（list 或 tuple）
- **THEN** 该 value 自动渲染为 `IndexedListPanel`（带索引的列表面板）

#### Scenario: str/value 逐字显示

- **WHEN** `__rich_detail__` yield 的 key 或 value 为 `str` 类型
- **THEN** 显示为纯文本，不解析 Rich markup（即使字符串中包含 `[bold]` 等 markup 标记）

#### Scenario: None 值显示

- **WHEN** `__rich_detail__` yield 的 value 为 `None`
- **THEN** 显示为 `"None"` 文本（附 `cx.detail.none` 样式）

### Requirement: `__rich_console__` MUST yield 渲染对象

所有组件的 `__rich_console__` 实现 MUST yield 渲染对象（`Generator[RenderableType, None, None]`），MUST NOT 直接调用 `console.render()` 返回结果。直接返回会绕过 Rich 的渲染管线（measurement、样式传递等）。此范式适用于 `WealthyDocument`、`Node`、`WealthyHelp`、`MaxColumnsLayout` 等所有实现 `__rich_console__` 的组件。

#### Scenario: 所有 `__rich_console__` 使用 yield

- **WHEN** 审查任意组件的 `__rich_console__` 方法
- **THEN** 方法体使用 `yield` / `yield from` 返回渲染对象，不存在 `return console.render(...)` 或等价的直接返回模式

#### Scenario: 空内容 yield

- **WHEN** `MaxColumnsLayout` 接收到空的渲染对象集合
- **THEN** yield 空的 `Group` 对象，不 raise 异常

### Requirement: `rich_types` 仅作对外便利出口

`rich_types` 模块 MUST 是对外便利出口，提供 Rich 高频类型的收窄别名。库内部模块 MUST 一律使用 `from rich.xxx import Xxx` 的真实路径导入 Rich 类型，MUST NOT 通过 `rich_types` 模块导入。新增 Rich 类型时内部直接 import，零成本，不需要同步注册到 `rich_types`。

#### Scenario: 内部不通过 `rich_types` 导入

- **WHEN** 查阅 `cx_wealthy` 包内除 `rich_types.py` 以外的任意模块
- **THEN** 该模块中不出现 `from .rich_types import` 或 `from ..rich_types import` 的导入语句

#### Scenario: 外部使用方通过 `rich_types` 获取类型

- **WHEN** 使用方执行 `from cx_wealthy.rich_types import Table, Text`
- **THEN** 获得与 `from rich.table import Table` 等价的类型对象，导出边界可控

### Requirement: 显式 `__all__` 导出

每个公开模块 MUST 定义 `__all__` 列表显式列出所有导出符号。`__init__.py` MUST 逐一列出每个导出符号，MUST NOT 使用 `from .module import *` 的 star-import 汇聚公开符号。此约定确保不泄漏 `typing`、`Literal` 等第三方符号到导出边界之外。

#### Scenario: star-import 不出现于 `__init__.py`

- **WHEN** 查阅 `cx_wealthy/__init__.py`
- **THEN** 不存在 `from .module import *` 形式的导入，所有导出通过显式 `__all__` 列表和逐条 import 语句声明

#### Scenario: 不泄漏第三方符号

- **WHEN** 使用方执行 `import cx_wealthy` 后检查 `dir(cx_wealthy)`
- **THEN** 结果中不包含 `typing`、`Literal`、`Any` 等不属于 `cx_wealthy` 公开 API 的符号

### Requirement: 私有命名无双下划线

内部辅助方法 MUST 使用单下划线前缀（如 `_render_label`、`_check_value`），MUST NOT 使用双下划线前缀。双下划线触发 Python 的 name mangling 机制，子类无法 override 该方法。

#### Scenario: 内部辅助方法使用单下划线

- **WHEN** 查阅 `cx_wealthy` 包内任意类的辅助方法
- **THEN** 辅助方法名以单下划线开头（如 `_xxx`），不存在 `__xxx`（非 dunder）形式的辅助方法

### Requirement: 最小依赖链

cx-wealthy 的 `pyproject.toml` `dependencies` MUST 仅包含 `rich>=14.0.0`。MUST NOT 依赖 `cx-studio` 或其他 cx 系列包。所需的基础工具函数（分隔符插入、locale 检测等短逻辑）MUST 在包内内联实现，不为短函数引入整包依赖。与 `cx-studio` 在依赖层面平级；`cxalio-studio-tools` 同时依赖两者。

#### Scenario: 依赖仅含 rich

- **WHEN** 查阅 `cx-wealthy/pyproject.toml` 的 `dependencies` 字段
- **THEN** 列表中仅包含 `rich>=14.0.0`，无其他依赖项

#### Scenario: 基础工具函数内联

- **WHEN** 使用分隔符插入或 locale 检测功能
- **THEN** 实现位于 `cx_wealthy` 包内（内联或包内私有模块），不通过 `import cx_studio` 获取

### Requirement: 不做 i18n

cx-wealthy MUST NOT 创建 `i18n/` 模块或在包内提供国际化基础设施。组件输出的框架固定文本（面板标题、占位符等）MUST 直接书写，不经过 `_()` 本地化包装。

#### Scenario: 无 i18n 模块

- **WHEN** 查阅 `cx_wealthy` 的包结构
- **THEN** 不存在 `i18n/` 目录或 `i18n.py` 文件

#### Scenario: 无 `_()` 包装

- **WHEN** 使用 grep 在 `cx_wealthy` 包内搜索 `_()` 本地化调用模式
- **THEN** 不存在匹配结果

### Requirement: 不做 argparse 包装器

`WealthyHelp` MUST NOT 提供 `from_argparse(parser)` 或类似的 argparse 适配器方法。`WealthyHelp` 保持解析器无关的声明式排版能力，不绑定任何参数解析方案。

#### Scenario: 无 argparse 适配器

- **WHEN** 查阅 `WealthyHelp` 类的方法列表
- **THEN** 不存在 `from_argparse`、`_from_argparse` 或类似名称的适配器方法

### Requirement: 主题透明性

组件不持有主题。`WealthyDocument` 和 `WealthyHelp` MUST NOT 具备 `styles`、`theme`、`DEFAULT_STYLES` 等属性，MUST NOT 在渲染时导入或补全任何主题。组件内 `style="cx.*"` 等样式名是约定，由调用方通过 `Console(theme=...)` 决定样式值。当调用方未设置 cx 主题时，`cx.*` 样式名 MUST 静默不生效（Rich 默认行为），内容仍完整可读。组件 MUST NOT 使用 Rich 私有 API（如 `console._theme_stack`）来检测或补全缺失样式。`default_theme` 与各样式字典在 `theme.py` 定义并对外导出，供调用方按需引用或覆盖。

#### Scenario: 缺失主题时内容完整

- **WHEN** 使用未配置 cx 主题的默认 `Console` 渲染 `WealthyDocument` 或 `WealthyHelp`
- **THEN** 所有文字内容完整显示，`cx.*` 样式名静默不生效（回退到 Rich 默认样式），不 raise 异常

#### Scenario: 组件无主题属性

- **WHEN** 检查 `WealthyDocument` 或 `WealthyHelp` 实例的属性
- **THEN** 不存在 `styles`、`theme`、`DEFAULT_STYLES` 属性

#### Scenario: 不使用 Rich 私有 API

- **WHEN** 使用 grep 在 `cx_wealthy` 包内搜索 `console._`、`_theme_stack` 等 Rich 内部 API 引用
- **THEN** 不存在匹配结果

### Requirement: MaxColumnsLayout 诚实命名与行为

`MaxColumnsLayout` MUST 仅执行固定最大列数 + 平均宽度分配的布局，MUST NOT 执行基于内容宽度的动态列数测量。构造参数 `max_columns` 指定允许的最大列数，实际列数取 `min(max_columns, len(items))`。空集合输入 MUST 渲染为空的 `Group`。

#### Scenario: 固定列数布局

- **WHEN** 创建 `MaxColumnsLayout` 并传入 3 个渲染对象，设置 `max_columns=2`
- **THEN** 渲染为两列布局，第三项换行至第二行；不做内容宽度测量以决定列数

#### Scenario: 空集合渲染

- **WHEN** `MaxColumnsLayout` 接收到空的渲染对象集合
- **THEN** yield 空的 `Group` 对象，不 raise 异常

#### Scenario: max_columns 约束

- **WHEN** `max_columns` 小于 1
- **THEN** 构造时 raise `ValueError`

### Requirement: IndexedListPanel 索引列表展示

`IndexedListPanel` MUST 为列表项添加行号索引，以 `Panel` 包裹 `Table` 形式渲染。渲染策略：优先使用项的 `__rich__` 协议；若实现 `__rich_label__` 则通过 `RichLabel` 包装为标签文本；否则退回到字符串表示。

#### Scenario: 列表项渲染优先级

- **WHEN** `IndexedListPanel` 接收到混合类型列表
- **THEN** 实现 `__rich__` 的项按原协议渲染，实现 `__rich_label__` 的项经包装渲染，其余项按 `str()` 渲染

### Requirement: `__rich_label__` 协议是可选的

`__rich_label__` 和 `__rich_detail__` 是并列的可选协议。使用方 MUST 按展示场景二选一或都实现，MUST NOT 为实现而写空的协议方法或抛 `NotImplementedError`（mixin 基类的默认实现除外）。不是所有领域对象都适合键值面板展示。

#### Scenario: 不实现也不报错

- **WHEN** 使用方的对象未实现 `__rich_label__` 或 `__rich_detail__`
- **THEN** 该对象作为普通渲染对象传给 `console.print()` 时，由 Rich 的默认渲染管线处理，不触发协议相关异常
