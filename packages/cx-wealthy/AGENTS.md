# cx-wealthy 工作区指南

> 本文件是根目录 `AGENTS.md` 在 `cx-wealthy` 工作区的特化补充。全局约定（命名、类型标注、Git workflow、版本策略、i18n 政策等）见根文件，此处不重述。本文件仅记录本工作区独有的定位、设计原则、协议定义与代码风格偏离点。

## 定位

`cx-wealthy` 是基于 [Rich](https://github.com/Textualize/rich) 的终端结构化文档与 UI 组件库，提供两大核心能力：

1. **通用结构化文档系统**——基于复合树的声明式文档构建与主题化渲染。帮助系统只是其特化之一，任何"分组 + 条目 + 注释"的结构化输出都可使用。
2. **双渲染协议**——`__rich_label__`（紧凑标签）+ `__rich_detail__`（键值面板），通过 mixin 让领域对象自身可被 `console.print()` 直接渲染。

**双重定位**：本包首先是 cx 系列自用的 Rich 扩展，同时作为独立库可供任何人使用。沿用 Rich 自身的 mixin 命名风格、提供 `rich_types` 便利出口等设计均在此定位下进行——对内服务于 cx 系列工具，对外不绑定 cx 系列的依赖与惯例。

**依赖**：仅 `rich>=14.0.0`。不依赖 `cx-studio`——UI 库应保持单一职责与最小依赖链。所需的基础工具函数（分隔符插入、locale 检测）逻辑很短，在包内内联实现，不为短函数引入整包依赖。

**依赖关系**：与 `cx-studio` 无依赖关系，两者在依赖层面平级；`cxalio-studio-tools` 同时依赖两者。`cx-wealthy` 仍是 cx- 系列的一员，提供 `cx.*` 命名空间的主题样式预设（纯数据导出，不引入依赖）。

## 核心设计原则

### 通用核心与特化分层

`document/` 是通用复合树核心（`Node`/`Group`/`Note`/`WealthyDocument`），`help/` 是帮助系统特化层（`Action`/`WealthyHelp` 继承 `WealthyDocument`）。通用核心不知道 flags/nargs/usage 为何物。

合并两者会导致通用核心的稳定性被 help 的迭代绑架——help 一变通用核心就要跟着变。且通用复合树被封装在 help 内部时，使用方不会想到它还能渲染非帮助类的结构化文档，能力被埋没。

### mixin + 包装器双轨

渲染协议用 mixin 承载（非 Protocol）：mixin 提供默认 `__rich__` 实现，使 `console.print(obj)` 直接输出正确渲染——"协议即渲染"。同时提供包装器（`RichLabel`/`WealthyDetailPanel`）给不愿或不能继承的使用方（第三方类型、frozen dataclass 继承位已满等）。两者共享底层渲染逻辑。

Protocol-only 不可取：Protocol 不允许带方法体，"协议即渲染"无法成立——所有使用方都必须显式 `console.print(RichLabel(obj))`，丢失直接打印的体验。mixin 只定义方法不定义字段，与 frozen dataclass 完全兼容，无实质冲突。

### rich_types 仅作对外便利出口

`rich_types` 模块是给使用方的 `r` 别名出口（与项目 `r` 约定一致），收窄到高频类型。**库内部一律用真实 import 路径**（`from rich.table import Table`）。

内部用别名会损失 IDE 跳转精度、类型推断绕一道、grep 无法区分真实类型与别名。新增 Rich 类型时内部直接 import 零成本，不需要同步注册到 rich_types。

### 标准渲染范式

所有 `__rich_console__` 实现**必须 yield 渲染对象**，禁止直接调用 `console.render()` 返回。直接返回会绕过 Rich 的渲染管线。

### 诚实命名

组件命名必须反映实际行为。例如列布局组件命名为 `MaxColumnsLayout`（固定最大列数 + 平均宽度），而非暗示动态测量的名字——除非真正实现了基于内容宽度的动态列数计算。名实不符会误导使用方对 API 契约的预期。

### 不做 i18n

**cx-wealthy 完全不需要国际化和本地化。** 本包不创建 `i18n/` 模块。作为 UI 组件库，其自身输出的文字（面板标题、占位符等）属于框架固定文本，由使用方控制而非库自行翻译。创建空壳 i18n 模块后，每次新增字符串都要思考"要不要包 `_()`"，这个心智负担在零翻译需求下是纯成本。若未来确有需求，按项目既有 i18n 方案落地。

### 不做 argparse 包装器

`WealthyHelp` 不提供 `from_argparse(parser)` 适配器。argparse 的扁平字段信息不足以驱动声明式排版，且生态中已有大量 argparse 美化器。本包的价值在于独立于任何解析器的声明式排版能力。

## 渲染协议定义

本包是 `__rich_label__` / `__rich_detail__` 双渲染协议的定义者。根 AGENTS 描述了协议的基本形态，此处补充定义性约定。

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

`__rich_detail__` 吸收了 `__rich_repr__` 的去重能力（三元组），但保留展示视角的渲染策略链。复用 `__rich_repr__` 替代 `__rich_detail__` 会丢失嵌套渲染、展示视角格式化、与 IndexedListPanel/RichLabel 的协同——这些是 detail 面板的核心价值。

### 协议是可选的

`__rich_label__` 和 `__rich_detail__` 是并列的可选协议——使用方按展示场景二选一或都实现，不应为实现而写空的协议方法或抛 `NotImplementedError`。不是所有领域对象都适合键值面板展示。

## 否决方案记录

以下方案在本包设计中被提出并否决，记录理由以防重新提出。每条只记否决依据，不记方案细节。

1. **复用 `__rich_repr__` 替代 `__rich_detail__`**——repr 的 value 由 `Pretty` 渲染（repr 风格），没有"value 若实现同协议则自动嵌套为 sub-panel"的约定，丢失嵌套展示能力。展示场景使用方需要预格式化（如 `str(path)` → 文件名而非 `PosixPath('/foo/bar')`），repr 期望 raw 值，复用会强制使用方在 yield 前自行包装，更繁琐。

2. **Protocol-only（不提供 mixin 默认实现）**——"协议即渲染"无法成立，所有使用方都必须显式包装，与 Rich 自身"`__rich__` 即渲染"的约定背离。

3. **Wrapper-only（不提供 mixin，只用包装器）**——detail 面板的 value 若是可展示对象，需要该对象**自身具备 `__rich__`** 才能自动以标签形态嵌套渲染。包装器 `RichLabel(obj)` 是外层包装，`obj` 自身没有 `__rich__`，在 detail 面板中作为 value 时不会被识别为可渲染对象。mixin 让对象自身具备 `__rich__`，是 detail 嵌套渲染的前置依赖。

4. **不分层，全部塞在 help/ 里**——通用核心的稳定性被 help 的迭代绑架；通用复合树被封装在 help 内部时，使用方不会想到它还能渲染非帮助类结构化文档。

5. **依赖 cx-studio**——本包对 cx-studio 的唯一潜在需求是短工具函数（分隔符插入约 10 行、locale 检测约 10 行），内联即可实现，为这些引入整包依赖不划算。

6. **照搬项目 i18n 惯例创建 i18n 模块**——本包没有需要翻译的字符串，空壳 i18n 模块引入心智负担且违反项目硬约束（空翻译文件有覆盖 msgid 的风险）。

7. **提供 `from_argparse(parser)` 适配器**——argparse 的扁平字段不足以驱动声明式排版，包装产出的排版无法达到独立构建的灵活度；生态有成熟 argparse 美化器，不应在此重复。

8. **在初始版本直接做真正的动态列测量**——真正基于 `Measurement.get` 的动态测量复杂度被低估，且单点需求不足以验证必要性。诚实命名（`MaxColumnsLayout`）比名实不符更好。

## 代码风格特化

以下约定与根 AGENTS 的通用规则存在偏离或补充，仅适用于本工作区。

### 导出：显式 `__all__`，不用 star-import

根 AGENTS 规定"每个子包通过 `__init__.py` star-import 汇聚公开符号"。**本包偏离此规则**：每个模块定义 `__all__`，`__init__.py` 显式列出每个导出符号。目的：不泄漏 `typing`/`Literal` 等第三方符号，导出边界可控。

### Rich 类型引用：内部真实路径

根 AGENTS 规定"依赖 cx-wealthy 的包必须通过 rich_types 引用 Rich 类型"。**本包特化此规则**：该约束针对使用方，不针对本包内部。库内部模块用 `from rich.table import Table` 真实路径，`rich_types` 仅作对外便利出口。

### 私有命名：无双下划线

内部辅助方法用单下划线前缀（如 `_render_label`、`_check_value`），不用双下划线。双下划线触发 name mangling，子类无法 override。

### 主题透明性

组件不持有主题——`WealthyDocument` / `WealthyHelp` 均无 `styles` / `theme` / `DEFAULT_STYLES` 属性，也不在渲染时导入或补全任何主题。组件内 `style="cx.*"` 等样式名是**约定**，由调用方通过 `Console(theme=...)` 决定样式值。

- **cxalio tools**：在 `IAppEnvironment` 中 `Console(theme=cx_default_theme)` 应用 cx 主题
- **第三方使用方**：不设主题时 `cx.*` 样式静默不生效（Rich 默认行为），内容仍完整可读；需样式时导入 `default_theme` 设为 Console 主题

`default_theme` 与 `BASE_STYLES` / `HELP_STYLES` / `DETAIL_STYLES` / `INDEXED_LIST_STYLES` 等常量在 `theme.py` 定义并对外导出，供调用方按需引用或覆盖。

组件**不使用** Rich 私有 API（如 `console._theme_stack`）。曾考虑在 `__rich_console__` 中检测缺失样式并兜底补全，但因依赖私有 API 被否决——没有公开 API 能实现"选择性补全缺失样式但不覆盖用户定义"，而无条件的 `console.use_theme(default_theme)` 会覆盖调用方自定义的 `cx.*` 样式，违反透明性。


## 扩展判断原则

本库作为 UI 组件库，天然面临"提前抽象"的诱惑——每个组件看起来都可复用，每个渲染分支看起来都可策略化，每个特化场景看起来都可泛化。

**扩展的触发条件是"第二个真实使用场景出现"，不是"技术上能做到更灵活"。** 当某场景只有一个使用方时，让使用方用 Rich 原生 API 凑合，而非提取入库。需求不出现的点保持简单，这是正确状态，不是待办。
