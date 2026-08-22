# cx-wealthy

基于 [Rich](https://github.com/Textualize/rich) 的终端结构化文档与 UI 组件库：既提供基于复合树的通用结构化文档系统（帮助系统只是其特化之一），也定义 `__rich_label__` / `__rich_detail__` 双渲染协议，让领域对象自身可被 `console.print()` 直接渲染。

## 定位

- **两大核心能力**：
  1. **通用结构化文档系统**——基于复合树的声明式文档构建与主题化渲染。帮助系统只是其特化之一，任何"分组 + 条目 + 注释"的结构化输出都可使用。
  2. **双渲染协议**——`__rich_label__`（紧凑标签）+ `__rich_detail__`（键值面板），通过 mixin 让领域对象自身可被 `console.print()` 直接渲染。
- **双重定位**：本包首先是 cx 系列自用的 Rich 扩展，同时作为独立库可供任何人使用。沿用 Rich 自身的 mixin 命名风格、提供 `rich_types` 便利出口等设计均在此定位下进行——对内服务于 cx 系列工具，对外不绑定 cx 系列的依赖与惯例。
- **依赖**：仅 `rich>=14.0.0`。不依赖 `cx-studio`——UI 库应保持单一职责与最小依赖链。所需的基础工具函数（分隔符插入、locale 检测）逻辑很短，在包内内联实现，不为短函数引入整包依赖（决策背景见 `docs/adr/0009`）。
- **依赖关系**：与 `cx-studio` 无依赖关系，两者在依赖层面平级；`cxalio-studio-tools` 同时依赖两者。`cx-wealthy` 仍是 cx- 系列的一员，提供 `cx.*` 命名空间的主题样式预设（纯数据导出，不引入依赖）。

## 渲染协议定义

本包是 `__rich_label__` / `__rich_detail__` 双渲染协议的定义者。根 AGENTS 描述了协议的基本形态，此处为定义性约定。

### `__rich_label__`：紧凑标签

- yield 一组 Renderable 片段，用分隔符拼接为单行 `Text`
- 用于列表行标题、行内摘要等紧凑场景
- `RichLabelMixin` 提供默认 `__rich__`，`RichLabel` 是包装器，共享同一套渲染逻辑

### `__rich_detail__`：键值面板

- yield `(key, value)` 或 `(key, value, default)` 三元组；三元组中 `value == default` 时该行不显示（去重）
- value 若实现同协议则自动嵌套渲染为 sub-panel；value 为列表自动渲染为 `IndexedListPanel`
- `RichDetailMixin` 提供默认 `__rich__`（包装为 `WealthyDetailPanel`），`WealthyDetailPanel`/`WealthyDetailTable` 是包装器

**key/value 的字符串语义**：

- `str` 类型的 key/value → 逐字显示，不解析 markup（数据安全）
- `Text` 类型的 key/value → 保留已有样式（用于需要 markup 的展示标签）
- 需要 markup 格式的 key/value，yield `Text.from_markup(...)` 而非裸字符串

这与 `__rich_label__` 的默认行为不同——label 的片段是展示字符串（`_fragment_to_text` 默认解析 markup），detail 的 value 是领域数据（默认逐字显示）。

### `__rich_detail__` ≠ `__rich_repr__`

两者不互相替代，语义不同：

| 维度 | `__rich_repr__`（Rich 原生） | `__rich_detail__`（本包） |
|---|---|---|
| 语义 | debug repr——"对象长什么样" | 展示——"对象该展示哪些字段" |
| value 渲染 | `Pretty`（repr 风格，raw 值） | 递归 sub-panel / IndexedListPanel / RichLabel 协同 |
| 格式化 | raw 值交给 Pretty | 使用方可预格式化（如 `str(path)`） |

`__rich_detail__` 吸收了 `__rich_repr__` 的去重能力（三元组），但保留展示视角的渲染策略链（否决「复用 `__rich_repr__` 替代 `__rich_detail__`」的理由见 `docs/adr/0002`）。

### 协议是可选的

`__rich_label__` 和 `__rich_detail__` 是并列的可选协议——使用方按展示场景二选一或都实现，不应为实现而写空的协议方法或抛 `NotImplementedError`。不是所有领域对象都适合键值面板展示。

## 约定

以下约定与根 AGENTS 的通用规则存在偏离或补充，仅适用于本工作区。

### 导出：显式 `__all__`，不用 star-import

根 AGENTS 规定"每个子包通过 `__init__.py` star-import 汇聚公开符号"。**本包偏离此规则**：每个模块定义 `__all__`，`__init__.py` 显式列出每个导出符号。目的：不泄漏 `typing`/`Literal` 等第三方符号，导出边界可控。

### Rich 类型引用：内部真实路径

根 AGENTS 规定"依赖 cx-wealthy 的包必须通过 rich_types 引用 Rich 类型"。**本包特化此规则**：该约束针对使用方，不针对本包内部。库内部模块用 `from rich.table import Table` 真实路径，`rich_types` 仅作对外便利出口（决策背景见 `docs/adr/0003`）。

### 私有命名：无双下划线

内部辅助方法用单下划线前缀（如 `_render_label`、`_check_value`），不用双下划线。双下划线触发 name mangling，子类无法 override。

### 主题透明性

组件不持有主题——`WealthyDocument` / `WealthyHelp` 均无 `styles` / `theme` / `DEFAULT_STYLES` 属性，也不在渲染时导入或补全任何主题。组件内 `style="cx.*"` 等样式名是**约定**，由调用方通过 `Console(theme=...)` 决定样式值。

- **cxalio tools**：在 `IAppEnvironment` 中 `Console(theme=cx_default_theme)` 应用 cx 主题
- **第三方使用方**：不设主题时 `cx.*` 样式静默不生效（Rich 默认行为），内容仍完整可读；需样式时导入 `default_theme` 设为 Console 主题

`default_theme` 与 `BASE_STYLES` / `HELP_STYLES` / `DETAIL_STYLES` / `INDEXED_LIST_STYLES` 等常量在 `theme.py` 定义并对外导出，供调用方按需引用或覆盖。

组件**不使用** Rich 私有 API（如 `console._theme_stack`）。曾考虑在 `__rich_console__` 中检测缺失样式并兜底补全，但因依赖私有 API 被否决——没有公开 API 能实现"选择性补全缺失样式但不覆盖用户定义"，而无条件的 `console.use_theme(default_theme)` 会覆盖调用方自定义的 `cx.*` 样式，违反透明性。

## Language

**WealthyDocument**：
`document/` 中通用复合树的根节点类型，声明式结构化文档的入口；`WealthyHelp` 继承自它。
_Avoid_: 帮助文档（那是 `WealthyHelp` 的特化职责）

**Node**：
`document/` 中复合树的节点基类，一切可嵌套结构元素的公共基础。
_Avoid_: 通用树节点（不体现复合树与渲染协议的关系）

**Group**：
复合树的"分组"节点，承载"分组 + 条目 + 注释"结构中的分组职责。

**Note**：
复合树的"注释"节点，承载"分组 + 条目 + 注释"结构中的注释职责。

**WealthyHelp**：
`help/` 帮助系统特化层的根类型，继承 `WealthyDocument`，组织 `Action` 条目。
_Avoid_: WealthyDocument（通用核心，不包含帮助语义）

**Action**：
`help/` 特化层中的帮助条目，描述单个命令/动作的展示单元。
_Avoid_: 通用条目（不携带命令/动作语义）

**RichLabel**：
`__rich_label__` 协议的包装器，给不愿或不能继承 `RichLabelMixin` 的使用方（第三方类型、frozen dataclass 等）使用。
_Avoid_: RichLabelMixin（那是供继承的默认实现，不是包装入口）

**RichDetailMixin**：
提供 `__rich_detail__` 默认 `__rich__` 实现的 mixin，使对象自身可渲染为 `WealthyDetailPanel`——"协议即渲染"。
_Avoid_: Protocol（mixin 可带方法体，Protocol 不能）

**WealthyDetailPanel**：
`__rich_detail__` 键值面板的 Panel 形态包装器，与 `RichDetailMixin` 共享同一套渲染逻辑。
_Avoid_: WealthyDetailTable（那是 Table 形态）

**WealthyDetailTable**：
`__rich_detail__` 键值面板的 Table 形态包装器，与 `RichDetailMixin` 共享同一套渲染逻辑。
_Avoid_: WealthyDetailPanel（那是 Panel 形态）

**IndexedListPanel**：
`__rich_detail__` 中 value 为列表时的自动渲染形态——带索引的列表面板。

**MaxColumnsLayout**：
列布局组件，固定最大列数 + 平均宽度；不暗示也不实现基于内容宽度的动态测量（决策背景见 `docs/adr/0005`）。
_Avoid_: 带"动态/自适应"含义的布局名

**rich_types**：
对外便利出口模块，收窄到高频 Rich 类型，供使用方以 `r` 别名引用；库内部一律用真实 import 路径（决策背景见 `docs/adr/0003`）。
_Avoid_: 内部模块直接 import rich_types

**cx.\* 样式名**：
组件内 `style="cx.*"` 形式的样式名约定，样式值由调用方通过 `Console(theme=...)` 决定，组件自身不持有主题。

**__rich_label__**：
紧凑标签渲染协议——yield 一组 Renderable 片段，用分隔符拼接为单行 `Text`，用于列表行标题、行内摘要等紧凑场景。
_Avoid_: __rich_detail__（那是键值面板，不是紧凑标签）

**__rich_detail__**：
键值面板渲染协议——yield `(key, value)` 或 `(key, value, default)` 三元组，value 递归 sub-panel / `IndexedListPanel` / `RichLabel` 协同渲染。
_Avoid_: __rich_repr__（那是 debug repr 语义，不是展示语义）
