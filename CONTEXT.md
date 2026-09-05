# CONTEXT —— 仓库统一领域文档

本仓库（cx-studio-tk）为 uv workspace 单仓，含三个 workspace：`cx-studio`（基础设施库）、`cx-wealthy`（Rich UI 组件库）、`cxalio-studio-tools`（CLI 工具集与共享框架）。领域文档统一存放于本文件与 `docs/adr/`（单一编号序列）——处理 `packages/` 下某 workspace 的内容时，阅读本文件对应 `## Domain:` 分区与 `docs/adr/` 中适用范围覆盖该 workspace 的 ADR；消费规则见 `docs/agents/domain.md`。根 `AGENTS.md` 为全局规范基线（跨领域通用规则），优先于本文档。

## Domain：cx-studio
> 适用范围：cx-studio

monorepo 中所有包的基础设施库，提供值对象、系统抽象、文件操作、FFmpeg 封装等通用能力。不放业务逻辑或特定工具的实现。

### 架构

重组后共 8 个子包，按"领域/功能"维度划分：

|子包|职责|核心符号|
|---|---|---|
|`core/`|基础值对象与工具函数|`CxTime`, `Timebase`, `TimeRange`, `FileSize`, `NumberRange`, `quick_clamp`, `quick_remap`, `flatten_list`, `iter_with_separator`, `split_to_two`|
|`text/`|文本处理|字符串工具、Shell 转义、`TagReplacer`、`PathInfoProvider`|
|`filesystem/`|文件系统操作|`PathUtils`, `CmdFinder`, `PathExpander`, `FileList`, `FileSizer`, `FileInfoCache`, `detect_file_encoding`|
|`system/`|系统抽象|`SystemType`, `CrossRunner`, `system_open`, `is_user_admin`|
|`clikit/`|CLI 工具基础设施|`DoubleTrigger`, `FIRST_TRIGGERED`, `SECOND_TRIGGERED`|
|`process/`|子进程与流处理|同步/异步版本的子进程创建、流读写、行解析|
|`ffmpeg/`|FFmpeg 封装|同步/异步执行器、编码信息数据类、错误类型层级、参数预处理器|
|`i18n/`|国际化基础设施|`gettext` 工厂函数、locale 检测、本地化文本加载器|

#### 内部依赖规则

严格遵守，不可反向：

```
i18n        ← 无内部依赖
core        → i18n
text        → core, i18n
process     → i18n
filesystem  → core, i18n, process
system      → i18n
clikit      → i18n
ffmpeg      → core, filesystem, process, i18n
```

### 约定

#### 文件命名

- 模块文件名不含 `cx_` 前缀（包名 `cx_studio` 已提供命名空间）
- 例外：去前缀后与 Python 标准库模块重名时，保留 `cx_` 前缀。同一"系列"的模块统一处理
  - 当前仅 `core/cx_time.py` 与 stdlib `time` 冲突，故 `cx_time.py`、`cx_timebase.py`、`cx_timerange.py` 保留前缀
- 新增模块直接使用短命名

#### 导出约定

- 每个子包通过 `__init__.py` 使用 `from .module import *` 汇聚所有公开符号
- 对外暴露的类/函数使用明确的公开名（无下划线前缀），内部实现使用 `_` 前缀
- 必要时在 `__init__.py` 中定义 `__all__` 列表

#### 禁止放入 cx-studio 的内容

- 特定 CLI 工具的业务逻辑 → 属于 `cxalio-studio-tools`
- Rich UI 组件 → 属于 `cx-wealthy`
- 应用生命周期管理 → 属于 `cx_tools.app`
- 只被单一工具使用的专用代码 → 放该工具内部

#### 添加新子包的检查清单

1. 是否至少包含 3+ 个有意义且相互关联的模块？若不足 3 个，考虑放入现有子包
2. 是否属于"通用基础设施"？若仅被一个工具使用，放该工具内部
3. 是否与现有子包存在明确的边界？新子包的定位不与已有子包重叠

### Language

**CxTime**：
core 包的基础时间值对象，毫秒级精度；属多年积累的时间域核心资产，直接兼容工业时间码标准（见 ADR 0001）。
_Avoid_: 用 `datetime`/`time` 表达时间码语义

**Timebase**：
时间基准（时基/帧率）描述对象，与 CxTime 同属时间域核心资产，兼容工业标准。

**TimeRange**：
时间范围值对象，描述一段起止时间；同属时间域核心资产，将来可用于时间线解析。

**FileSize**：
文件大小值对象，封装大小表示与换算。

**NumberRange**：
数值范围值对象。

**PathUtils**：
filesystem 包以模块方式提供的路径工具命名空间，承载通用路径操作。

**CmdFinder**：
可执行命令查找器，用于定位命令。

**PathExpander**：
路径展开器，展开含通配符/变量的路径。

**FileList**：
文件列表对象，承载文件系统扫描/枚举结果。

**FileSizer**：
文件大小计算器。

**FileInfoCache**：
文件信息缓存。

**SystemType**：
系统抽象层的平台类型标识，抽象系统差异。

**CrossRunner**：
跨平台运行器，屏蔽平台差异执行命令。

**system_open**：
跨平台"用系统默认程序打开"操作。

**is_user_admin**：
判断当前用户是否具备管理员权限。

**DoubleTrigger**：
clikit 的 CLI 双击触发基础设施，与 `FIRST_TRIGGERED` / `SECOND_TRIGGERED` 状态常量配合实现双击判定。

**TagReplacer**：
text 包的文本标签替换器，用于模板/占位符替换。

## Domain：cx-wealthy
> 适用范围：cx-wealthy

基于 [Rich](https://github.com/Textualize/rich) 的终端结构化文档与 UI 组件库：既提供基于复合树的通用结构化文档系统（帮助系统只是其特化之一），也定义 `__rich_label__` / `__rich_detail__` 双渲染协议，让领域对象自身可被 `console.print()` 直接渲染。

### 定位

- **两大核心能力**：
  1. **通用结构化文档系统**——基于复合树的声明式文档构建与主题化渲染。帮助系统只是其特化之一，任何"分组 + 条目 + 注释"的结构化输出都可使用。
  2. **双渲染协议**——`__rich_label__`（紧凑标签）+ `__rich_detail__`（键值面板），通过 mixin 让领域对象自身可被 `console.print()` 直接渲染。
- **双重定位**：本包首先是 cx 系列自用的 Rich 扩展，同时作为独立库可供任何人使用。沿用 Rich 自身的 mixin 命名风格、提供 `rich_types` 便利出口等设计均在此定位下进行——对内服务于 cx 系列工具，对外不绑定 cx 系列的依赖与惯例。
- **依赖**：仅 `rich>=14.0.0`。不依赖 `cx-studio`——UI 库应保持单一职责与最小依赖链。所需的基础工具函数（分隔符插入、locale 检测）逻辑很短，在包内内联实现，不为短函数引入整包依赖（决策背景见 `docs/adr/0010`）。
- **依赖关系**：与 `cx-studio` 无依赖关系，两者在依赖层面平级；`cxalio-studio-tools` 同时依赖两者。`cx-wealthy` 仍是 cx- 系列的一员，提供 `cx.*` 命名空间的主题样式预设（纯数据导出，不引入依赖）。

### 渲染协议定义

本包是 `__rich_label__` / `__rich_detail__` 双渲染协议的定义者。根 AGENTS 描述了协议的基本形态，此处为定义性约定。

#### `__rich_label__`：紧凑标签

- yield 一组 Renderable 片段，用分隔符拼接为单行 `Text`
- 用于列表行标题、行内摘要等紧凑场景
- `RichLabelMixin` 提供默认 `__rich__`，`RichLabel` 是包装器，共享同一套渲染逻辑

#### `__rich_detail__`：键值面板

- yield `(key, value)` 或 `(key, value, default)` 三元组；三元组中 `value == default` 时该行不显示（去重）
- value 若实现同协议则自动嵌套渲染为 sub-panel；value 为列表自动渲染为 `IndexedListPanel`
- `RichDetailMixin` 提供默认 `__rich__`（包装为 `WealthyDetailPanel`），`WealthyDetailPanel`/`WealthyDetailTable` 是包装器

**key/value 的字符串语义**：

- `str` 类型的 key/value → 逐字显示，不解析 markup（数据安全）
- `Text` 类型的 key/value → 保留已有样式（用于需要 markup 的展示标签）
- 需要 markup 格式的 key/value，yield `Text.from_markup(...)` 而非裸字符串

这与 `__rich_label__` 的默认行为不同——label 的片段是展示字符串（`_fragment_to_text` 默认解析 markup），detail 的 value 是领域数据（默认逐字显示）。

#### `__rich_detail__` ≠ `__rich_repr__`

两者不互相替代，语义不同：

| 维度 | `__rich_repr__`（Rich 原生） | `__rich_detail__`（本包） |
|---|---|---|
| 语义 | debug repr——"对象长什么样" | 展示——"对象该展示哪些字段" |
| value 渲染 | `Pretty`（repr 风格，raw 值） | 递归 sub-panel / IndexedListPanel / RichLabel 协同 |
| 格式化 | raw 值交给 Pretty | 使用方可预格式化（如 `str(path)`） |

`__rich_detail__` 吸收了 `__rich_repr__` 的去重能力（三元组），但保留展示视角的渲染策略链（否决「复用 `__rich_repr__` 替代 `__rich_detail__`」的理由见 `docs/adr/0003`）。

#### 协议是可选的

`__rich_label__` 和 `__rich_detail__` 是并列的可选协议——使用方按展示场景二选一或都实现，不应为实现而写空的协议方法或抛 `NotImplementedError`。不是所有领域对象都适合键值面板展示。

### 约定

以下约定与根 AGENTS 的通用规则存在偏离或补充，仅适用于本工作区。

#### 导出：显式 `__all__`，不用 star-import

根 AGENTS 规定"每个子包通过 `__init__.py` star-import 汇聚公开符号"。**本包偏离此规则**：每个模块定义 `__all__`，`__init__.py` 显式列出每个导出符号。目的：不泄漏 `typing`/`Literal` 等第三方符号，导出边界可控。

#### Rich 类型引用：内部真实路径

根 AGENTS 规定"依赖 cx-wealthy 的包必须通过 rich_types 引用 Rich 类型"。**本包特化此规则**：该约束针对使用方，不针对本包内部。库内部模块用 `from rich.table import Table` 真实路径，`rich_types` 仅作对外便利出口（决策背景见 `docs/adr/0004`）。

#### 私有命名：无双下划线

内部辅助方法用单下划线前缀（如 `_render_label`、`_check_value`），不用双下划线。双下划线触发 name mangling，子类无法 override。

#### 主题透明性

组件不持有主题——`WealthyDocument` / `WealthyHelp` 均无 `styles` / `theme` / `DEFAULT_STYLES` 属性，也不在渲染时导入或补全任何主题。组件内 `style="cx.*"` 等样式名是**约定**，由调用方通过 `Console(theme=...)` 决定样式值。

- **cxalio tools**：在 `IAppEnvironment` 中 `Console(theme=cx_default_theme)` 应用 cx 主题
- **第三方使用方**：不设主题时 `cx.*` 样式静默不生效（Rich 默认行为），内容仍完整可读；需样式时导入 `default_theme` 设为 Console 主题

`default_theme` 与 `BASE_STYLES` / `HELP_STYLES` / `DETAIL_STYLES` / `INDEXED_LIST_STYLES` 等常量在 `theme.py` 定义并对外导出，供调用方按需引用或覆盖。

组件**不使用** Rich 私有 API（如 `console._theme_stack`）。曾考虑在 `__rich_console__` 中检测缺失样式并兜底补全，但因依赖私有 API 被否决——没有公开 API 能实现"选择性补全缺失样式但不覆盖用户定义"，而无条件的 `console.use_theme(default_theme)` 会覆盖调用方自定义的 `cx.*` 样式，违反透明性。

### Language

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
列布局组件，固定最大列数 + 平均宽度；不暗示也不实现基于内容宽度的动态测量（决策背景见 `docs/adr/0006`）。
_Avoid_: 带"动态/自适应"含义的布局名

**rich_types**：
对外便利出口模块，收窄到高频 Rich 类型，供使用方以 `r` 别名引用；库内部一律用真实 import 路径（决策背景见 `docs/adr/0004`）。
_Avoid_: 内部模块直接 import rich_types

**cx.\* 样式名**：
组件内 `style="cx.*"` 形式的样式名约定，样式值由调用方通过 `Console(theme=...)` 决定，组件自身不持有主题。

**__rich_label__**：
紧凑标签渲染协议——yield 一组 Renderable 片段，用分隔符拼接为单行 `Text`，用于列表行标题、行内摘要等紧凑场景。
_Avoid_: __rich_detail__（那是键值面板，不是紧凑标签）

**__rich_detail__**：
键值面板渲染协议——yield `(key, value)` 或 `(key, value, default)` 三元组，value 递归 sub-panel / `IndexedListPanel` / `RichLabel` 协同渲染。
_Avoid_: __rich_repr__（那是 debug repr 语义，不是展示语义）

## Domain：cxalio-studio-tools
> 适用范围：cxalio-studio-tools

`packages/cxalio-studio-tools/` 是包含 6 个 CLI 工具（media_scout、media_killer、ffpretty、jpegger、hosts_keeper、cxnote）与共享框架 `cx_tools` 的分发包。所有工具均构建在 `cx_tools.app` 应用框架之上，共享统一的应用生命周期管理、Rich 输出与中断处理。

### 架构

#### 三层分层

CLI 工具采用三层分层，确保各层职责清晰、可独立复用：

1. **环境层（IAppEnvironment / `<Tool>Env`）**——全局交互能力
   - 职责：say/whisper 输出、中断处理、banner 显示；具体子类按需提供 progress，不覆盖 say/whisper
   - 特征：单例，但不被 Application 绑定
   - 互不依赖：不持有 context，不解析参数

2. **上下文层（IAppContext / `<Tool>Context`）**——参数 + 运行状态
   - 职责：参数解析结果、运行时状态（temp_dir 等）、惰性能力
   - 特征：实现上下文管理器协议（`__enter__`/`__exit__` + start/stop）
   - 生命周期：由 Application 管理

3. **应用层（IApplication / Application）**——编排器
   - 职责：组装 appenv + context，驱动生命周期
   - 特征：不绑定特定 appenv 单例，可被复用
   - 生命周期：`__enter__` 启动 context，`__exit__` 停止 context；appenv 上下文在 Application 外部管理

#### 层间依赖规则

- Application 依赖 appenv 和 context，通过构造参数注入
- 子组件透明接收 context/appenv/progress（按需），不接收 parent 引用
- appenv 和 context 互不依赖
- 基础设施层（cx_studio）不依赖任何 CLI 组件

#### 组件分层

CLI 工具中的所有类按是否依赖运行环境分为两层：

**CLI 特化组件** — 继承 `IAppComponent`。`IAppComponent.__init__` 提供 `(appenv, context)` 签名契约，子类在 `__init__` 中按需自行存储 `appenv`/`context`，不通过基类 property 访问。包括：
- `IApplication` 子类（通过 IApplication 继承 IAppComponent）
- 直接接收 appenv + context 的支撑组件（HostsBuilder、HostsSaver、ProfileManager、MissionRunner 等）

**通用功能组件** — 不继承 `IAppComponent`，不依赖 appenv/context/env。包括：
- 值对象/dataclass（Mission、Preset、HostRecord 等）
- 纯算法/IO 类（MediaDB、MissionExecutor、SourceExpander、ScriptMaker、PresetLoader 等）
- 纯过滤器/处理器（jpegger 的 ImageFilterChain 及全部过滤器）

规则：
- 新组件如果需要调用 `appenv.say()`/`appenv.whisper()` 或读取 `context` 字段 → 继承 `IAppComponent`
- 新组件如果只做算法/IO/数据处理 → 不继承 `IAppComponent`，保持通用性
- 只需要 `IAppEnvironment`（不需要 context）的组件 → 接收 `env: IAppEnvironment` 参数，不继承 IAppComponent（如 MissionHQ）
- 只需要 `appenv` 的可选耦合 → 用 `appenv=None` 可选参数（如 UrlContenter）

#### 工具内部分层：common / components

工具包内部按能力归属分两层：

- **`common/`** — 不需要 appenv 的非耦合能力（对外提供面）。如 ffpretty.common（Mission/Executor/MediaDB）、media_killer.common（MissionHQ 调度层）、media_scout.common（inspectors）。
- **`components/`** — 需要 appenv 或含工具特定转化/包装逻辑的组件。如 ffpretty.components（mission_runner/mission_maker/info_elements）、media_killer.components（preset/expander/script_maker/mission_store）。

判别标准 = **appenv 依赖 + 特化与否**：不依赖 appenv 且非工具特定 → common；否则 → components。公共能力在设计之初规划（非消费者驱动），避免事后从 components 反向抽取。

**组合面契约**：工具间 import 只允许指向 `package.common`（可到 `package.common.subpackage`，如 `ffpretty.common.executor` 的事件常量）；ToolApp/ToolHelp 一级内容可从包根直接导入。不提供 common 的工具（hosts_keeper、jpegger）不强制区分 common/components。

### 工具编写模式

所有 CLI 工具遵循统一的编写模式，共享相同的应用生命周期和基础设施。

#### CLI 入口点

每个工具在 `__init__.py` 定义 `run()`，负责组装依赖并启动应用：

```python
def run() -> None:
    context = <Tool>Context.from_arguments(sys.argv[1:])
    appenv = <Tool>Env()
    with appenv:
        with Application(appenv=appenv, context=context, progress=appenv.progress) as app:
            app.run()
```

`Application` 命名随工具变化（`Application`、`FFPrettyApp`、`JpeggerApp`），但均实现 `IApplication`。
Application 通过构造参数接收 `appenv` 和 `context`；progress 是工具特定子类的构造参数（从 `appenv.progress` 获取），不在 IApplication 接口中。不导入全局单例。

#### 参数解析

每个工具使用 `<Tool>Context` 类（`from_arguments()` 唯一工厂，`kwargs` 白名单赋值），不直接暴露 argparse。

#### 帮助系统

每个工具使用 `WealthyHelp` DSL（`add_group`/`add_action`/`add_note` 声明式构建），帮助文件通过 `cx_studio.i18n.load_localized_text()` 加载（按 locale 自动选择 `help.md` / `help.<locale>.md`）。

#### 异常体系

`SafeError`（可恢复应用异常，带 style）由 `Application.__exit__` 捕获。

#### 分级输出

`IAppEnvironment` 提供 `say()`（始终显示）和 `whisper()`（仅 debug 模式）两个输出层级。详见下方"输出通道"。

#### 输出通道

`IAppEnvironment.console` 初始化为 `stderr=True`，因此 `say()` 和 `whisper()` 的输出均走 **stderr**。stdout 保留给用户可能通过管道重定向的数据输出。

##### 三者的选择

| 函数               | 通道   | 何时使用                                                 |
| ------------------ | ------ | -------------------------------------------------------- |
| `appenv.say()`     | stderr | 始终显示的用户提示，如操作结果、错误信息、完成状态       |
| `appenv.whisper()` | stderr | 仅 debug 模式（`-d`）下显示，如内部诊断细节              |
| 内置 `print()`     | stdout | 用户需要管道获取的数据内容，如 pretend 模式下的输出结果 |

> 通常不直接使用 print 函数，而是在 appenv 中初始化一个新的 Console 负责 stdout 输出。

##### 规则

- 所有用户可见的提示性文字必须使用 `say()` 或 `whisper()`。禁止裸 `console.print()` 调用（banner 例外，见下文）。
- 数据类输出（如"假装模式下显示将要写入的内容"）使用 `print()`，确保管道可用。
- `say()` 内部强制开启高亮器（`highlight=True`），会按正则匹配文件路径、数字、命令行参数等并附加样式。如需避免高亮器干扰（如 ASCII art），将内容包裹在 `r.Text(style=...)` 中——显式 style 的 Text 对象不受高亮器影响。

### 应用环境与 UI

#### Banner 显示

工具启动时显示 banner。推荐模式：

```python
banner_text = importlib.resources.read_text(__package__, "banner.txt", ...)
banners.append(r.Align.center(r.Text(banner_text, style="bold cyan", no_wrap=True, overflow="crop")))
banners.append(r.Align.center(r.Text(_("标语"), style="bold cyan")))
self.say(r.Group(*banners))
```

要点：

- 每个元素用 `r.Text(style=...)` 包裹，赋予显式样式，阻止高亮器覆盖。
- 使用 `self.say()` 输出，保持输出通道统一。
- 不使用 `console.print(group, style=..., highlight=False)` 绕过 `say()`。

#### Progress 与输出时序

Progress 用 `console=self.console` 创建。Rich Live 接管该 console 的输出——`self.console.print()`（基类 `say()`/`whisper()` 调用的方法）在 Live 运行期间会自动暂停 Live 渲染、输出文本、恢复 Live，无需手动 stop/start progress。`<Tool>Env` 子类不应 override `say()`/`whisper()` 来协调 progress。

##### 约束

1. **`transient=True`**——所有 `Progress` 实例必须设为 `transient=True`。设置后 progress 在 `stop()` 时自动清屏，不滞留上次运行的状态。`transient=False` 仅在需要保留进度历史时有意义，未经讨论不得使用。

2. **警惕 generator 延迟执行**——若进度构建逻辑封装在返回 generator 的函数中，函数体在被迭代之前不会执行。以下顺序错误：

   ```
   gen = builder.build(profiles)  # generator，未执行
   progress.stop()                # 过早——实际工作还没开始
   for x in gen:                  # 实际执行在这里
   ```

   正确顺序：

   ```
   gen = builder.build(profiles)
   for x in gen:                  # 先耗尽 generator
       ...
   progress.stop()                # 再停 progress
   ```

#### __exit__ 覆盖模式

工具自定义 `__exit__` 必须遵循以下结构：

```python
@override
def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
    result = super().__exit__(exc_type, exc_val, exc_tb)  # 始终先走正常清理（stop + context 清理）
    if exc_type is KeyboardInterrupt:                      # 按需处理具体异常
        self.appenv.say(f"[cx.error]{_('用户中断')}[/]")
        result = True
    return result
```

要点：

- `super().__exit__()` 始终优先执行，确保 `stop()`（工具特定清理）和 `context.__exit__()`（临时目录删除等）不因异常类型跳过。
- 返回 `True` 抑制异常传播（用户提示已由 `say()` 输出），返回 `False` 或 `None` 则异常继续传播。

#### 中断处理

##### 策略 A：`__exit__` 中 catch KeyboardInterrupt

适用于不需要多次 Ctrl+C 取消流程的工具。在 `Application.__exit__` 中直接检查 `exc_type is KeyboardInterrupt`，无需注册 signal handler。见上方 `__exit__` 覆盖模式示例。

##### 策略 B：DoubleTrigger 信号机制

`IAppEnvironment` 内置 `DoubleTrigger` 对象。在 `<Tool>Env.__init__` 中注册回调：

```python
@self.interrupt_handler.on("first_triggered")
def _when_wanna_quit():
    self.wanna_quit_event.set()

@self.interrupt_handler.on("second_triggered")
def _when_really_wanna_quit():
    self.really_quit_event.set()
```

在模块末尾注册 signal handler：

```python
signal.signal(signal.SIGINT, appenv.handle_interrupt)
```

首次 Ctrl+C 触发 `first_triggered`（设置 `wanna_quit_event`，提示用户再次确认）。再次 Ctrl+C 触发 `second_triggered`（设置 `really_quit_event`，强制中断）。适用于有长时间异步操作需要优雅取消的工具。

##### 策略选择原则

- 同步代码路径（如 hosts_keeper 的 for 循环）→ 策略 A（KeyboardInterrupt），不注册 signal handler
- 异步代码路径（如 media_killer 的 asyncio loop）→ 策略 B（DoubleTrigger + signal handler），但必须用手动 event loop（`run_async()`）而非 `asyncio.run()`，否则 Python 3.13 会覆盖 SIGINT handler

### 引用模式

#### Application 组装

Application 不再全局获取 appenv，而是通过构造参数注入。`__init__.py` 入口负责组装：

```python
def run() -> None:
    from rich.traceback import install
    install(...)
    context = <Tool>Context.from_arguments(sys.argv[1:])
    appenv = <Tool>Env()
    with appenv:
        with Application(appenv=appenv, context=context, progress=appenv.progress) as app:
            app.run()
```

#### appenv 单例

每个工具的 `appenv.py` 末尾仍定义模块级单例（用于 signal handler 注册）：

```python
appenv = <Tool>Env()
signal.signal(signal.SIGINT, appenv.handle_interrupt)
```

但 Application 和子组件不再通过 `from .appenv import appenv` 导入使用，而是通过构造参数接收。

#### i18n

每个工具自持 `i18n/` 模块和 `i18n/locales/` 翻译文件，不允许交叉导入。各工具从自己的 `i18n` 模块导入翻译函数：

| 工具 | 导入 |
| --- | --- |
| cx_tools（框架） | `from cx_tools.i18n import _, _ng` |
| media_scout | `from media_scout.i18n import _, _ng` |
| media_killer | `from media_killer.i18n import _, _ng` |
| ffpretty | `from ffpretty.i18n import _, _ng` |
| jpegger | `from jpegger.i18n import _, _ng` |
| hosts_keeper | `from hosts_keeper.i18n import _, _ng` |

#### 框架导入

共享框架类从 `cx_tools.app` 导入：

```python
from cx_tools.app import IAppEnvironment, ConfigManager
```

### Language

**IApplication**：
应用层接口，CLI 工具的编排器抽象——组装 appenv + context、驱动生命周期，可被复用。
_Avoid_: `Application`（工具内的具体实现类，命名随工具变化）

**IAppEnvironment**：
环境层接口，提供 say/whisper 分级输出、中断处理、banner 显示等全局交互能力；不持有 context、不解析参数。
_Avoid_: `<Tool>Env`（工具具体子类，按需提供 progress）

**IAppContext**：
上下文层接口，承载参数解析结果与运行时状态（temp_dir 等），实现上下文管理器协议。
_Avoid_: `<Tool>Context`（工具具体子类）

**IAppComponent**：
CLI 特化组件基类接口，`__init__` 仅提供 `(appenv, context)` 签名契约，不存储、不暴露（子类自行赋值）。

**SafeError**：
可恢复应用异常，带 style，由 `Application.__exit__` 捕获。

**WealthyHelp**：
帮助系统 DSL，通过 `add_group`/`add_action`/`add_note` 声明式构建帮助内容。

**DoubleTrigger**：
`IAppEnvironment` 内置的双次 Ctrl+C 信号机制，依次发出 `first_triggered` / `second_triggered` 事件。

**Mission**：
媒体处理任务的值对象/dataclass。
_Avoid_: MissionRunner、MissionExecutor、MissionHQ（调度/执行组件）

**MissionHQ**：
media_killer.common 的调度层组件；只依赖 `IAppEnvironment`（接收 `env` 参数，不继承 IAppComponent）。

**CrossRunner**：
hosts_keeper 的装饰器注册机制，要求模块级函数且签名固定——这是模块级 appenv 导入例外的根因。

**media_scout**：
CLI 工具，分析影视后期工程文件（XML/FCPXML/EDL/CSV/TXT）提取原始素材路径，输出到 stdout。

**media_killer**：
CLI 工具，解析 TOML 预设文件创建批量转码任务并调用 ffmpeg 执行；依赖 media_scout 的工程文件探测能力。

**ffpretty**：
CLI 工具，ffmpeg 的简单包装，直接透传所有参数并提供 Rich 进度条显示。

**jpegger**：
CLI 工具，批量图片处理，支持色彩空间转换、按比例缩放与多格式输出（JPEG/PNG/WebP 等）。

**hosts_keeper**：
CLI 工具，hosts 文件管理——多来源合并去重、规则筛选、自动更新、刷新 DNS 缓存（Windows/macOS）。

**cxnote**：
CLI 工具，终端快速笔记（包 `cx_note`）——以域组织的待办便签：快记字符串条目、按域浏览、跟踪待办状态并自动清理超龄已完成条目。

**域**：
cx-note 的字面命名空间——形如 `/a/b` 的路径式字符串，仅用作条目归属的组织单位，与文件系统目录结构无绑定；身份判定大小写不敏感，存储保留首次出现的字面。
_Avoid_: 目录、文件夹（域不映射目录结构）

**根域**：
域树的顶层 `/`，对应 $HOME；`-g` 参数是它的快捷指定方式。

**条目**：
cx-note 记录的最小单元——字符串内容（可含换行）、三态状态、创建/完成日期、所属域与 4 位 ID。

**删除**：
`erase` 命令执行的用户动作——按 ID 或文本片段定位并物理移除单条条目；被删除条目不可恢复。
_Avoid_: 清除（v1 术语，退役）、归档

**清空**：
`clear` 命令执行的用户动作——移除当前工作域自身全部条目（不含子域），执行前需确认；域无实体，清空后仍可再 `add`。与「删除」的区别在范围：整域 vs 单条。
_Avoid_: 清除

**清理**：
cx-note 对超龄已完成条目的自动维护——保存时顺带执行、仅限当前域、尽力而为不保证完备；未完成条目永不参与清理。与手动动作（删除/清空）的区别：清理是工具自动执行，删除/清空是用户发起。
