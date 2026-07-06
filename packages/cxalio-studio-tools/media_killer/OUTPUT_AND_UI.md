# media_killer 输出与 UI 设计文档

> 本文档规定 media_killer 基于 `cx_wealthy` 的输出策略、组件选用、主题使用方式以及进度条管理。
> 阅读对象：后续实现或维护 media_killer 的开发者；目标是在不依赖旧版 `cx_wealth` 的前提下，复现并改进旧版的终端表现。
>
> 关联文档：
> - [CLI_BEHAVIOR.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/CLI_BEHAVIOR.md) —— 用户可见行为锚点
> - [ARCHITECTURE.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md) —— 组件架构
> - `cx_wealthy` 源码：`packages/cx-wealthy/cx_wealthy/`

---

## 1. 总则：全面迁移到 cx_wealthy

### 1.1 基本立场

**media_killer 禁止使用 `cx_wealth`，统一使用 `cx_wealthy`。**

- `cx_wealth` 是旧版实现，已决定逐步废弃。
- `cx_wealthy` 是重新设计的 Rich 终端组件库，位于 `packages/cx-wealthy/`。
- 两者接口不同，不能简单替换 import 路径；需要按本文档重新选择组件与调用方式。

### 1.2 旧版组件 → 新版组件总览

| 旧版 `cx_wealth` | 新版 `cx_wealthy` | 说明 |
|---|---|---|
| `WealthHelp` | [`WealthyHelp`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/help/help.py) | 帮助文档顶层类；构造与渲染接口有变化 |
| `WealthDetailPanel` | [`WealthDetailPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/detail.py) | 键值详情面板；语义一致，构造参数有变化 |
| `WealthLabel` | [`RichLabel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/label.py) / [`RichLabelMixin`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/label.py) | 单行标签渲染包装器 / mixin |
| `IndexedListPanel` | [`IndexedListPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/indexed_list.py) | 带索引的列表面板；修复了旧版索引计算 bug |
| `DynamicColumns` | [`MaxColumnsLayout`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/columns.py) | 列布局；新版是“固定最大列数 + 平均宽度”，不再假装动态测量 |
| `rich_types`（别名出口） | `cx_wealthy.rich_types` | 继续作为 `r` 别名使用；内部代码应直接 import Rich 真实类型 |

### 1.3 为什么必须重新选型

- `cx_wealthy` 将通用文档核心与帮助系统分层，`WealthyHelp` 继承自 `WealthyDocument`；旧版 `WealthHelp` 是单一类。
- `cx_wealthy` 引入 `__rich_label__` / `__rich_detail__` 双协议，并提供 mixin + 包装器双轨支持；旧版只有 `WealthLabel` / `WealthDetailPanel` 包装器。
- `cx_wealthy` 的主题设计是**透明**的：组件只使用 `style="cx.*"` 等样式名，不持有主题。主题由调用方通过 `Console(theme=...)` 决定。旧版大量硬编码具体样式字符串，与新设计冲突。

---

## 2. 输出层级与通道

### 2.1 两级输出：say / whisper

沿用 `IAppEnvironment` 的约定（参见 `packages/cxalio-studio-tools/cx_tools/app/iappenv.py`）：

| 方法 | 可见性 | 样式/高亮 | 用途 |
|---|---|---|---|
| `appenv.say(...)` | 始终显示 | 开启高亮 (`highlight=True`) | 用户提示、结果、状态摘要 |
| `appenv.whisper(...)` | 仅在 `-d/--debug` 时显示 | 固定 `dim`，无高亮 | 诊断、细节、内部流程 |

### 2.2 通道：全部走 stderr

- `IAppEnvironment.console` 初始化时 `stderr=True`。
- 所有 `say()` / `whisper()` / `progress` 都走 stderr。
- stdout 保留给数据类输出；media_killer 当前没有数据类输出，因此 stdout 空闲。

### 2.3 高亮器行为

- `say()` 会强制开启 `CxHighlighter`，自动为以下内容附加样式：
  - 括号括起的内容 → `cx.brackets`
  - 引号字符串 → `cx.quotes`
  - 文件路径 → `cx.filepath`
  - 数字 → `cx.number`
  - 命令行参数（`-x` / `--xxx`） → `cx.argument`
- `whisper()` 不开启高亮，整体 `dim`。
- 如果不想让 `say()` 高亮器处理某段内容（如 banner 艺术字），应将其包装为带显式 `style` 的 `Text` 对象。

---

## 3. 各阶段输出内容

本节与 [CLI_BEHAVIOR.md §5](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/CLI_BEHAVIOR.md#5-执行阶段与用户可见输出) 对应，但专注于**使用什么组件、如何渲染、何时调用**。

> 标注约定：每个阶段下分 **`say()` 输出（用户始终可见）** 和 **`whisper()` 输出（仅 debug）** 两栏，严格区分。

### 3.1 启动阶段

**`say()` 输出（用户始终可见）**：

- banner 艺术字（从资源文件读取）
- 工具名 + 版本号
- 当前模式标签（模拟运行、安全模式、强制覆盖模式）
- 应用描述（无模式标签时）

**实现方式**：

- banner 文本用 `r.Text(..., style="cx.mk.banner", no_wrap=True, overflow="crop", justify="center")` 包装，再用 `r.Align.center(...)` 居中。`cx.mk.banner` 是 media_killer 自定义主题字段，默认 `bold red`。
- 工具名/版本/描述用 `r.Text.from_markup(...)` 组装，使用 `cx.info`、`cx.number` 等语义样式名。
- 模式标签使用 `cx.mk.mode.simulate`、`cx.mk.mode.safe`、`cx.mk.mode.force`。
- 用 `appenv.say(r.Group(...))` 一次性输出。

> 启动阶段无 `whisper()` 输出。

### 3.2 输入扫描阶段

**`say()` 输出（用户始终可见）**：

- 简洁状态摘要：
  ```
  检测到 {preset_count} 个配置文件：【1】【2】
  {source_count} 个来源文件
  ```
  或等价的单行汇总：`已添加 {preset_count} 个配置文件和 {source_count} 个来源路径。`
- 模式标签、覆盖决策等运行状态（如 `假装模式已启动`、`已启用强制覆盖`）。

> 注意：`say()` 中只显示数量与简要索引/标识；完整的文件路径、详情列表属于 debug 信息。

**`whisper()` 输出（仅 debug）**：

- 每个预设文件的完整详情：[`WealthDetailPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/detail.py) 包装 `Preset`。
- 完整来源路径列表：[`IndexedListPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/indexed_list.py)。
- 两个列表面板可以放进 [`MaxColumnsLayout`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/columns.py) 并排显示。

**实现方式**：

- `say()` 只输出状态摘要，不列出完整路径；`CxHighlighter` 会自动高亮摘要中的路径和数字。
- 具体文件/路径清单、完整详情全部下沉到 `whisper()`。

### 3.3 任务生成阶段

**`say()` 输出（用户始终可见）**：

- 继续模式恢复提示：`从上次执行中恢复了 {count} 个任务……`
- 本次生成任务数量：`生成了 {count} 个任务。`
- 去重/排序结果：
  - 有去重：`[cx.warning]已自动过滤掉 {diff} 个重复任务，共 {total} 个任务需要执行。[/]`
  - 无去重：`全部任务整理完毕，已按照设定方式排序。`
- 最终任务总数：`本次执行共 {total} 个转码任务。`

**`whisper()` 输出（仅 debug）**：

- 每个 Preset 生成的完整任务列表：[`IndexedListPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/indexed_list.py)。
- 去重/排序后的完整任务列表。
- Preset 与任务数量的并排摘要（debug 下展示）：`r.Columns([RichLabel(preset), Text(..., justify="right")], expand=True)`。
- 单个 Mission 的完整详情：[`WealthDetailPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/detail.py)。

**实现方式**：

- `say()` 只输出状态数字和简短结论，不展开列表。
- 统计数字使用 `cx.number`；警告/提示使用 `cx.warning` / `cx.success`。
- 完整任务清单、Preset 详情全部下沉到 `whisper()`。

### 3.4 脚本保存模式

**`say()` 输出（用户始终可见）**：

- 保存脚本文件后的确认行：`已保存脚本到：{filename}`

**`whisper()` 输出（仅 debug）**：

- 脚本内容列表：[`IndexedListPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/indexed_list.py)。

### 3.5 模拟运行模式

**`say()` 输出（用户始终可见）**：

- 模拟运行提示：`[cx.info]假装模式已启动[/]，将不会真正执行任何操作。`
- 每个 Mission 的完成/失败/取消结果行（参见 §5.5 和 §5.7 Mission 标识行颜色设计）。

**`whisper()` 输出（仅 debug）**：

- 模拟执行过程中的内部状态检查详情。

**实现方式**：

- 提示用 `appenv.say()` + `cx.info` 样式。
- 进度管理同真实执行阶段，只是底层 `MissionExecutor` 不调用 FFmpeg。

### 3.6 转码执行阶段

**`say()` 输出（用户始终可见）**：

- 总进度条 + 每个 Mission 的子进度条（`transient=True`，执行结束后自动消失）。
- Mission 完成/失败/取消的结果行（在进度条消失后输出）。

**`whisper()` 输出（仅 debug）**：

- Mission 开始前的完整参数：[`WealthDetailPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/detail.py) + 状态行。
- Mission 失败时的 FFmpeg 原始输出：[`IndexedListPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/indexed_list.py)。
- 被跳过的 Mission 的跳过原因（若用户指定 `-n` 且目标已存在）。

**实现方式**：

- 进度条由 `Progress` 组件管理，详见 [§5 Progress 设计](#5-progress-设计)。
- Mission 开始信息用 `appenv.whisper()`。
- Mission 结果行在进度条停止/消失后通过 `appenv.say()` 输出，避免与 progress 渲染冲突。

### 3.7 结束阶段

**`say()` 输出（用户始终可见）**：

- garbage 清理汇总：`已清理 {count} 个目标文件。`
- 输入/输出文件总大小（若大于 0）。
- 总耗时（若超过 5 秒）。
- `Bye ~`

**`whisper()` 输出（仅 debug）**：

- 每个被清理 garbage 文件的具体路径。

**实现方式**：

- `say()` 只输出汇总，不列出单个文件。
- 大小和耗时数字使用 `cx.number`。
- 清理提示使用 `cx.info` 或默认文本。
- 单个删除文件路径通过 `whisper()` 输出。

---

## 4. whisper 与 say 的格式和时机

**核心原则**：`say()` 输出状态摘要，`whisper()` 输出详细清单。具体文件列表、详细参数、原始 FFmpeg 输出等必须沉入 `whisper()`。

### 4.1 whisper 格式规范

- **触发条件**：仅当 `appenv.is_debug_mode_on()` 返回 `True`（即 `-d/--debug`）时输出。
- **样式**：固定 `dim`，不开启高亮。
- **内容**：内部状态、完整清单、开发诊断、详细参数。
- **典型场景（debug 专属）**：
  - 完整预设文件列表：[`IndexedListPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/indexed_list.py) / [`WealthDetailPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/detail.py)。
  - 完整来源路径列表：[`IndexedListPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/indexed_list.py)。
  - 完整任务列表：[`IndexedListPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/indexed_list.py)。
  - Mission 开始前的完整参数：[`WealthDetailPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/detail.py)。
  - Mission 失败时的 FFmpeg 原始输出：[`IndexedListPanel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/indexed_list.py)。
  - garbage 清理时每个被删除文件的具体路径。
  - 流程节点标记，如 "开始为预设 <name> 扫描源文件…"

### 4.2 say 格式规范

- **触发条件**：始终输出。
- **样式**：开启高亮；需要强调语义时使用 `cx.*` 样式名；Mission 标识行按 §5.7 颜色设计保留结构配色。
- **内容**：用户必须看到的状态摘要、结果、警告、错误。
- **必须简洁**，不展开列表。典型示例：
  - `检测到 {x} 个配置文件：【1】【2】`
  - `{y} 个来源文件`
  - `本次执行共 {m} 个转码任务。`
  - `假装模式已启动。`
  - `已启用强制覆盖。`
  - `已清理 {n} 个目标文件。`
  - `已完成 {m} 个任务中的 {n} 个。`
- **markup 使用规则**：
  - 推荐使用语义样式名：`[cx.info]`、`[cx.warning]`、`[cx.error]`、`[cx.success]`、`[cx.number]`、`[cx.filepath]`。
  - 禁止直接使用具体颜色名（如 `[red]`、`[blue]`）。所有颜色必须通过 `cx.*` 或 `cx.mk.*` 主题字段表达。
  - 动态内容若包含用户输入路径，优先依赖 `CxHighlighter` 自动识别，不要手动包 `[cx.filepath]`，除非需要精确控制。

### 4.3 不要与 Progress 同时大量输出

- `Progress` 与 `say()` 共用同一个 `Console`。
- 在 progress 活跃期大量调用 `say()` 可能导致部分终端渲染异常。
- Mission 完成后的结果行应在 progress 停止或该 Mission 的进度条消失后再输出。
- 具体策略：
  - 子进度条 `transient=True`，任务结束后自动消失；消失后再 `say()` 结果行。
  - 调试信息用 `whisper()`，由于 debug 模式用户已预期不稳定输出，可接受少量冲突。

---

## 5. Progress 设计

### 5.1 Progress 初始化

- 在 `AppEnv.__init__` 中初始化 `Progress`，包装全局 `console`。
- 必须设置 `transient=True`，保证进度条在完成后自动消失。
- 列布局建议：

```python
progress = Progress(
    SpinnerColumn(),
    TextColumn(
        "[progress.description]{task.description}",
        table_column=Column(ratio=60, no_wrap=True),
    ),
    BarColumn(table_column=Column(ratio=40)),
    TaskProgressColumn(justify="right"),
    TimeRemainingColumn(compact=True),
    console=self.console,
    transient=True,
    expand=True,
)
```

### 5.2 总进度条 vs 子进度条

| 进度条 | 任务 ID | 描述 | 总量 | 更新时机 |
|---|---|---|---|---|
| 总进度 | `total_task` | 显示总体速度和进度 | Mission 数量 或 总时长 | 每个 Mission 开始/完成/更新时 |
| 子进度 | 每个 Mission 一个 | 显示当前 Mission 的速度和描述 | 当前 Mission 的时长（若已知） | Mission 的 `progress_updated` 事件 |

### 5.3 子进度条描述格式

建议格式：

```
[{current}/{total}][{speed}x]{mission_name}
```

- `{current}/{total}`：任务编号 / 总数。
- `{speed}x`：当前编码速度（如 `1.25x`）。
- `{mission_name}`：Mission 名称（源文件基础名）。

使用 `Text.from_markup()` 组装。计数器、速度等结构部分按 §5.7 颜色设计；文件名推荐 `cx.info`。

### 5.4 进度更新频率

- 调度器主循环中每 0.1 秒更新一次。
- 不要在每次 FFmpeg stderr 行到达时都更新 progress，避免过度刷新。
- 进度事件在 `MissionExecutor` 中通过 `progress_updated` 事件发出；调度器批量读取后统一更新 Rich Progress。

### 5.5 进度条完成后的结果输出

- Mission 完成后，子进度条因 `transient=True` 已消失。
- 此时通过 `appenv.say()` 输出单行结果：
  - 成功：`[cx.success]完成[/] <mission_label>`
  - 失败：`[cx.error]运行异常[/] <mission_label>`
  - 取消：`[cx.info]被取消[/] <mission_label>` 或跳过提示。

### 5.6 为什么 progress 要包装全局 console

- `Progress` 默认会创建自己的 `Console`；若与 `say()`/`whisper()` 不共用同一 console，会出现两个独立渲染目标，导致输出交错、主题不一致。
- 通过 `console=self.console` 确保所有输出共享同一主题和高亮器。

### 5.7 Mission 标识行与结果行颜色设计（保留旧版用心设计）

旧版在进度条描述和任务完成提示前都使用了一段带颜色区分的 Mission 标识行，其中包含一个 `JobCounter`（任务计数器）。该设计用于让用户在密集输出中快速识别任务身份、当前进度和状态，新版必须保留。所有颜色均通过 §7.3 中定义的 `cx.mk.*` 主题字段表达。

**标识行格式**：

```
[cx.mk.mission.type]M[/] [cx.mk.mission.metadata][{preset_name}:{inputs}->{outputs}][/] [cx.mk.mission.name]{mission_name}[/]
```

或简化为（用于 progress description）：

```
[cx.mk.mission.counter][{current}/{total}][/][cx.number][{speed}x][/][cx.mk.mission.name]{mission_name}[/]
```

**颜色分工**：

| 片段 | 主题字段 | 含义 | 默认样式 |
|---|---|---|---|
| `M` | `cx.mk.mission.type` | 类型标识（Mission） | `bold bright_black` |
| `[preset:inputs->outputs]` | `cx.mk.mission.metadata` | 来源预设与输入输出数量 | `dim green` |
| `[{current}/{total}]` | `cx.mk.mission.counter` | 任务计数器（JobCounter） | `bright_black` |
| `[{speed}x]` | `cx.number` | 当前编码速度 | `cyan` |
| `{mission_name}` | `cx.mk.mission.name` | 源文件名（最需关注） | `yellow` |
| 源文件目录 | `cx.mk.mission.source` | 源文件所在目录 | `italic dim blue` |
| 状态 `完成` | `cx.success` | 成功 | `bold green` |
| 状态 `运行异常` | `cx.error` | 失败 | `bold red` |
| 状态 `开始` | `cx.mk.status.start` | 开始 | `yellow` |
| 状态 `被取消` | `cx.mk.status.cancelled` | 取消/跳过 | `bright_blue` |

**结果行格式示例**：

```
[cx.mk.mission.type]M[/] [cx.mk.mission.metadata][{preset_name}:{inputs}->{outputs}][/] [cx.mk.mission.name]{mission_name}[/] [cx.success]完成[/]
```

**实现方式**：

- 在 `Mission` 上实现 `__rich_label__()`，按上述格式 yield 片段，全部使用 `cx.mk.*` 字段。
- `JobCounter` 可直接复用 `cx_studio.tui.tools.job_counter.JobCounter`，用于生成 `{current}/{total}` 对齐字符串。
- `MissionScheduler` 在更新 progress description 时，使用 `RichLabel(mission)` 或 `mission.__rich__()` 作为基础，再追加 `JobCounter`、速度和状态。
- 任务完成/失败/取消后，调用 `appenv.say(RichLabel(mission) + 状态文本)`，保持与进度条中一致的视觉结构。

**为什么保留这种多色结构**：

- `M` 和计数器使用 `cx.mk.mission.type` / `cx.mk.mission.counter`（默认 `bright_black`）弱化，避免与文件名竞争注意力。
- 预设信息使用 `cx.mk.mission.metadata`（默认 `dim green`），提供上下文但不抢眼。
- 文件名使用 `cx.mk.mission.name`（默认 `yellow`），是用户最关心的部分。
- 状态词单独着色（`cx.success` / `cx.error` / `cx.mk.status.start` / `cx.mk.status.cancelled`），让用户一眼区分成功/失败/取消。

**被否决的替代方案**：

- **整行使用单一语义样式**：会丢失旧版通过颜色快速定位任务身份和状态的能力。
- **完全移除 `M` 标识和计数器**：在并发任务多、进度条快速切换时，用户难以区分当前是哪条任务。
- **将结果行输出到 whisper**：任务完成状态是必须让用户始终可见的信息，不应仅 debug 显示。
- **继续硬编码具体颜色**：违反新版"所有颜色必须走主题字段"的原则，无法通过主题覆盖。

---

## 6. 组件映射与使用规范

### 6.1 WealthyHelp（帮助）

旧版：

```python
from cx_wealth import WealthHelp

class MKHelp(WealthHelp):
    def __init__(self):
        super().__init__(prog="mediakiller")
```

新版：

```python
from cx_wealthy import WealthyHelp

class MKHelp(WealthyHelp):
    def __init__(self):
        super().__init__(prog="mediakiller")
```

差异：

- 类名从 `WealthHelp` 变为 `WealthyHelp`。
- `add_action()` 参数基本一致，但底层 `Action` 类独立在 `cx_wealthy.help.action` 中。
- `render()` 现在返回 Generator，调用方直接用 `console.print(MKHelp())` 即可。

### 6.2 WealthDetailPanel / WealthDetailTable（详情）

旧版：

```python
from cx_wealth import WealthDetailPanel
appenv.whisper(WealthDetailPanel(mission, title=str(mission.mission_id)))
```

新版：

```python
from cx_wealthy import WealthDetailPanel
appenv.whisper(WealthDetailPanel(mission, title=str(mission.mission_id)))
```

差异：

- 构造参数基本相同，但 `WealthDetailTable` 拆分为独立类。
- `Mission` 应实现 `__rich_detail__()` 协议；也可以继承 `RichDetailMixin` 自动获得 `__rich__()`。
- `__rich_detail__()` 中 `str` 类型的 value 会被**逐字显示**，不会解析 markup；如需 markup，应 yield `Text.from_markup(...)`。

### 6.3 IndexedListPanel（索引列表）

旧版：

```python
from cx_wealth import IndexedListPanel
appenv.whisper(IndexedListPanel(self.sources, _("来源路径列表")))
```

新版：

```python
from cx_wealthy import IndexedListPanel
appenv.whisper(IndexedListPanel(self.sources, title=_("来源路径列表")))
```

差异：

- `title` 必须作为关键字参数传入。
- 修复了旧版的索引起始值和最后一行计算 bug。
- 列表项若实现 `__rich__` 或 `__rich_label__`，会自动按正确方式渲染。

### 6.4 RichLabel / RichLabelMixin（标签）

旧版 `WealthLabel` 是包装器，新版对应 [`RichLabel`](file:///d:/workspace/cx-studio-tk/packages/cx-wealthy/cx_wealthy/label.py)。

推荐两种用法：

1. **Mixin 方式**（领域对象直接可渲染）：

```python
from cx_wealthy import RichLabelMixin

class Mission(RichLabelMixin):
    def __rich_label__(self):
        yield "[cx.mk.mission.type]M[/]"
        yield f"[cx.mk.mission.metadata][[{self.preset_name}]:{len(self.inputs)}->{len(self.outputs)}][/]"
        yield f"[cx.mk.mission.name]{self.name}[/]"
```

2. **包装器方式**（第三方类型或 frozen dataclass 继承位已满）：

```python
from cx_wealthy import RichLabel
label = RichLabel(mission)
```

注意：

- `__rich_label__()` 的片段默认**解析 markup**。
- 如需关闭 markup，使用 `RichLabel(obj, markup=False)`。

### 6.5 MaxColumnsLayout（列布局）

旧版 `DynamicColumns`：

```python
from cx_wealth import DynamicColumns
appenv.whisper(DynamicColumns(WealthDetailPanel(...) for x in self.presets))
```

新版：

```python
from cx_wealthy import MaxColumnsLayout
appenv.whisper(MaxColumnsLayout(
    (WealthDetailPanel(x, title=x.id) for x in self.presets),
    max_columns=2,
))
```

差异：

- 类名变为 `MaxColumnsLayout`，更诚实反映其“固定最大列数 + 平均宽度”的行为。
- 不再假装动态测量列宽；对 media_killer 的场景已足够。
- 返回 `Table.grid` 而非 `Columns`。

### 6.6 原生 Rich 组件

以下场景直接使用 Rich 原生组件，不需要 cx_wealthy 包装：

| 场景 | 组件 | 说明 |
|---|---|---|
| banner 居中 | `Align.center` + `Text` | banner 是艺术字，不需要 cx_wealthy 结构化 |
| 多行组合 | `Group` / `rich.console.Group` | 组装多个渲染对象 |
| 单行左右分栏 | `Columns` | 如 Preset 名称在左、任务数量在右 |
| 简单文本 | `Text` / `Text.from_markup` | 用于组装描述字符串 |
| Markdown 教程 | `Markdown` | `--tutorial` 显示完整教程 |

---

## 7. 主题策略

### 7.1 核心原则：语义主题字段，禁止硬编码具体颜色

旧版代码中大量存在 `"[bold blue]"`、`"[yellow]"`、`"[red]"` 等硬编码颜色。新版要求：

- **所有渲染代码必须使用语义主题字段名**（`cx.*` 或 `cx.mk.*`），禁止使用具体颜色名。
- **可复用的通用语义**优先使用 `cx_wealthy` 已定义的 `cx.info`、`cx.warning`、`cx.error`、`cx.success`、`cx.number`、`cx.filepath`、`cx.whisper` 等。
- **media_killer 特有的视觉角色**通过注入自定义主题字段 `cx.mk.*` 实现，确保设计质量与语义并存。
- **debug 输出**统一走 `whisper()`，由 `IAppEnvironment` 自动应用 `dim`，代码中不手动加颜色。

### 7.2 为什么 media_killer 需要自己的主题字段

旧版的 Mission 标识行、模式标签、banner 等并不是通用 UI 组件，而是 media_killer 特有的视觉语言：

- `M` 标识、`JobCounter`、元数据括号、文件名在标识行中有明确的层级分工。
- 模式标签（模拟运行 / 安全模式 / 强制覆盖）使用蓝 / 绿 / 红形成直觉区分。
- 这些颜色不能简单映射到 `cx.info`/`cx.success`/`cx.error`，否则会改变旧版精心设计的视觉层次。

因此 media_killer 在 `cx_wealthy.default_theme` 基础上扩展一组 `cx.mk.*` 字段，既保留设计风格，又让代码表达语义。

### 7.3 media_killer 自定义主题字段

推荐在 `media_killer.theme` 模块定义：

```python
from cx_wealthy import default_theme as cx_default_theme
from rich.theme import Theme

MEDIA_KILLER_STYLES: dict[str, str] = {
    # Mission 标识行组件
    "cx.mk.mission.type": "bold bright_black",      # M 类型标识
    "cx.mk.mission.counter": "bright_black",        # JobCounter [current/total]
    "cx.mk.mission.metadata": "dim green",          # [preset:inputs->outputs] 元数据括号
    "cx.mk.mission.name": "yellow",                 # 源文件名（视觉焦点）
    "cx.mk.mission.source": "italic dim blue",      # 源文件所在目录

    # Mission 执行状态（无法直接映射到 cx.success/cx.error 的中性状态）
    "cx.mk.status.start": "yellow",                 # 开始
    "cx.mk.status.cancelled": "bright_blue",        # 被取消 / 跳过

    # 运行模式标签
    "cx.mk.mode.simulate": "blue",                  # 模拟运行
    "cx.mk.mode.safe": "green1",                    # 安全模式
    "cx.mk.mode.force": "red",                      # 强制覆盖

    # 应用品牌
    "cx.mk.banner": "bold red",                     # banner 艺术字
}

media_killer_theme = Theme({**cx_default_theme.styles, **MEDIA_KILLER_STYLES})
```

字段说明：

| 字段 | 默认样式 | 用途 | 为什么是必要的 |
|---|---|---|---|
| `cx.mk.mission.type` | `bold bright_black` | Mission/Preset 类型标识 `M`/`P` | 标识行中最弱化的固定前缀，无通用语义字段可替代 |
| `cx.mk.mission.counter` | `bright_black` | JobCounter `[current/total]` | 用户明确要求的独立字段；需要弱化显示 |
| `cx.mk.mission.metadata` | `dim green` | `[preset:inputs->outputs]` | 结构性元数据，需要统一且独立于文件名 |
| `cx.mk.mission.name` | `yellow` | 源文件名 | 标识行视觉焦点，需突出；`cx.info` 语义不符 |
| `cx.mk.mission.source` | `italic dim blue` | 源文件目录 | 补充信息，需弱化；`cx.whisper` 是 `dim` 但不含蓝色调 |
| `cx.mk.status.start` | `yellow` | 任务开始 | 中性通知状态，不是 warning/success/error |
| `cx.mk.status.cancelled` | `bright_blue` | 任务取消/跳过 | 中性终止状态，不是 error |
| `cx.mk.mode.simulate` | `blue` | 模拟运行标签 | 模式标签三色设计之一，映射到 `cx.info` 会变为 cyan |
| `cx.mk.mode.safe` | `green1` | 安全模式标签 | 模式标签三色设计之一，映射到 `cx.success` 会变成 bold green |
| `cx.mk.mode.force` | `red` | 强制覆盖标签 | 模式标签三色设计之一，映射到 `cx.error` 会变成 bold red |
| `cx.mk.banner` | `bold red` | banner 艺术字 | 应用品牌艺术字，允许作为独立字段 |

### 7.4 注入自定义主题

`AppEnv` 初始化时合并 `cx_wealthy.default_theme` 与 `MEDIA_KILLER_STYLES`：

```python
from cx_wealthy import default_theme as cx_default_theme
from media_killer.theme import MEDIA_KILLER_STYLES
from rich.theme import Theme

self.console = Console(
    stderr=True,
    theme=Theme({**cx_default_theme.styles, **MEDIA_KILLER_STYLES}),
    highlighter=self.highlighter,
    highlight=False,
)
```

### 7.5 复用 cx_wealthy 通用字段的场景

以下场景不新增 `cx.mk.*` 字段，直接使用 `cx_wealthy` 已有语义字段：

| 场景 | 使用字段 | 说明 |
|---|---|---|
| 成功状态 | `cx.success` | 语义与颜色均与旧版「完成」一致 |
| 错误状态 | `cx.error` | 语义与颜色均与旧版「运行异常」一致 |
| 警告提示 | `cx.warning` | 去重、重复配置文件等 |
| 数字 / 文件大小 | `cx.number` | 任务数量、速度、文件大小 |
| 文件路径 | `cx.filepath` | 完整路径高亮 |
| 弱化说明 | `cx.whisper` | 版本描述、源目录补充、debug 信息 |
| 普通信息 | `cx.info` | 工具名、版本号、普通提示 |

### 7.6 组件内样式约定

cx_wealthy 组件内部使用 `style="cx.*"` 作为约定，但不持有主题。调用方通过 `Console(theme=...)` 决定是否应用样式。

media_killer 作为调用方，应始终将合并后的主题传给 `Console`。

### 7.7 新版 markup 映射速查

| 旧版 markup | 新版 markup | 字段归属 |
|---|---|---|
| `[bold bright_black]M[/]` | `[cx.mk.mission.type]M[/]` | `cx.mk.*` |
| `[bright_black][{current}/{total}][/]` | `[cx.mk.mission.counter][{current}/{total}][/]` | `cx.mk.*` |
| `[dim green][preset:...][/]` | `[cx.mk.mission.metadata][preset:...][/]` | `cx.mk.*` |
| `[yellow]{name}[/]` | `[cx.mk.mission.name]{name}[/]` | `cx.mk.*` |
| `[italic dim blue]({dir})[/]` | `[cx.mk.mission.source]({dir})[/]` | `cx.mk.*` |
| `[green]{完成}[/]` | `[cx.success]{完成}[/]` | `cx_wealthy` |
| `[red]{运行异常}[/]` | `[cx.error]{运行异常}[/]` | `cx_wealthy` |
| `[yellow]{开始}[/]` | `[cx.mk.status.start]{开始}[/]` | `cx.mk.*` |
| `[bright_blue]{被取消}[/]` | `[cx.mk.status.cancelled]{被取消}[/]` | `cx.mk.*` |
| `[blue]{模拟运行}[/]` | `[cx.mk.mode.simulate]{模拟运行}[/]` | `cx.mk.*` |
| `[green1]{安全模式}[/]` | `[cx.mk.mode.safe]{安全模式}[/]` | `cx.mk.*` |
| `[red]{强制覆盖}[/]` | `[cx.mk.mode.force]{强制覆盖}[/]` | `cx.mk.*` |
| `[bold red]banner[/]` | `[cx.mk.banner]banner[/]` | `cx.mk.*` |
| 普通信息 `[blue]...[/]` | `[cx.info]...[/]` | `cx_wealthy` |
| 数字 `[cyan]...[/]` | `[cx.number]...[/]` | `cx_wealthy` |

### 7.8 为什么不完全禁止具体颜色

- banner 等艺术字依赖具体颜色表达视觉层次，强制语义化反而失去意义。通过 `cx.mk.banner` 等独立字段，艺术字的"具体颜色"被封装在主题中，代码仍使用语义名。
- 用户提示文本必须使用语义字段，以便用户通过主题覆盖统一调整。

---

## 8. 旧版代码改造清单

| 文件 | 旧版引用 | 新版改造 |
|---|---|---|
| `application.py` | `from cx_wealth import DynamicColumns, IndexedListPanel, WealthDetailPanel` | 改为 `from cx_wealthy import MaxColumnsLayout, IndexedListPanel, WealthDetailPanel`；详细列表面板下沉到 `whisper()`；硬编码颜色改为 `cx.*` |
| `appenv.py` | `from cx_wealth import rich_types as r` | 改为 `from cx_wealthy import rich_types as r`；banner/模式标签硬编码颜色需评估 |
| `mk_help_info.py` | `from cx_wealth import WealthHelp, rich_types` | 改为 `from cx_wealthy import WealthyHelp, rich_types` |
| `components/mission_runner.py` | `from cx_wealth import IndexedListPanel, WealthDetailPanel, rich_types` | 改为 `from cx_wealthy import IndexedListPanel, WealthDetailPanel, rich_types`；Mission 结果行保留 §5.7 多色标识设计；FFmpeg 输出下沉到 `whisper()` |
| `components/mission_maker.py` | `from cx_wealth import WealthLabel, IndexedListPanel, rich_types` | 改为 `from cx_wealthy import RichLabel, IndexedListPanel, rich_types`；生成的任务列表下沉到 `whisper()` |
| `components/script_maker.py` | `from cx_wealth import IndexedListPanel` | 改为 `from cx_wealthy import IndexedListPanel`；脚本内容列表下沉到 `whisper()` |
| `components/mission_arranger.py` | `from cx_wealth.wealth_label import WealthLabel` | 改为 `from cx_wealthy import RichLabel` |
| `components/mission.py` | `from cx_wealth import rich_types as r` | 改为 `from cx_wealthy import rich_types as r`；让 `Mission` 继承 `RichLabelMixin` 并按 §5.7 实现标识行 |

### 8.1 Mission 类的改造要点

旧版 `Mission.__rich__()` 手动组装 `Text`：

```python
def __rich__(self) -> r.Text:
    return r.Text.assemble(
        *[r.Text.from_markup(x) for x in iter_with_separator(self.__rich_label__(), " ")],
        overflow="crop",
    )
```

新版推荐：

```python
from cx_wealthy import RichLabelMixin

@dataclass(frozen=True)
class Mission(RichLabelMixin):
    ...

    def __rich_label__(self):
        yield "[cx.mk.mission.type]M[/]"
        yield f"[cx.mk.mission.metadata][[{self.preset_name}]:{len(self.inputs)}->{len(self.outputs)}][/]"
        yield f"[cx.mk.mission.name]{self.name}[/]"
        yield f"[cx.mk.mission.source]({self.source.parent})[/]"
```

或直接保留 `__rich__()` 但使用 `RichLabel(self)` 作为其实现。

> 说明：详见 §5.7 Mission 标识行颜色设计与 §7.3 `cx.mk.*` 主题字段。所有颜色均通过 `cx.mk.*` 主题字段表达，不再使用 `[yellow]`、`[dim green]`、`[italic dim blue]` 等硬编码颜色。

---

## 9. 已确认决策与被否决方案

### 9.1 使用 cx_wealthy 替代 cx_wealth

**选定方案**：media_killer 全面使用 `cx_wealthy`，禁止依赖 `cx_wealth`。

**被否决的替代方案**：

- **继续用 `cx_wealth` 实现新版**：违反项目硬约束，`cx_wealth` 将被废弃；两套组件库并行会增加维护成本。
- **直接复制 `cx_wealth` 代码到 media_killer**：破坏组件复用，后续 `cx_wealthy` 改进无法同步受益。

**理由**：`cx_wealthy` 是专门为 cx 系列工具重新设计的 Rich 扩展，主题透明、协议清晰、职责分层更好。

### 9.2 主题由 AppEnv 统一注入

**选定方案**：`AppEnv` 在初始化 `Console` 时合并 `cx_wealthy.default_theme` 与 media_killer 自定义的 `MEDIA_KILLER_STYLES`（`cx.mk.*`），统一注入。

**被否决的替代方案**：

- **每个组件内部导入并应用主题**：会破坏主题透明性，覆盖用户自定义主题，且依赖 Rich 私有 API（`console._theme_stack`）。
- **不使用主题，保留硬编码颜色**：无法通过主题统一调整，不同工具视觉风格难以一致。
- **只使用 `cx_wealthy.default_theme`，不为 media_killer 特有视觉角色增加字段**：会迫使 Mission 标识行、模式标签等映射到不匹配的通用字段，降低设计质量。

**理由**：`cx_wealthy` 的主题设计是“组件只约定样式名，调用方决定样式值”；media_killer 的 Mission 标识行、模式标签等是特有视觉语言，需要 `cx.mk.*` 字段精确表达语义并保留旧版设计质量。

### 9.3 Progress 与 say 共用同一 console

**选定方案**：`Progress` 初始化时通过 `console=self.console` 与 `say()`/`whisper()` 共用同一 `Console` 实例。

**被否决的替代方案**：

- **Progress 使用独立 Console**：会导致进度条和普通输出在不同渲染目标上交错，主题和高亮器不一致。
- **所有输出都通过 Progress 的 `console.print`**：会绕过 `say()`/`whisper()` 的分层语义和高亮控制。

**理由**：共用 console 保证主题、高亮、输出通道一致；`say()`/`whisper()` 仍负责输出层级，Progress 只负责进度条。

### 9.4 Mission 结果行在进度条消失后输出

**选定方案**：Mission 完成后，先让子进度条因 `transient=True` 消失，再通过 `appenv.say()` 输出结果行。

**被否决的替代方案**：

- **在进度条运行期间直接 `say()` 结果**：会导致进度条和文字输出竞争同一行，部分终端渲染异常。
- **完全不输出 Mission 结果行**：用户无法得知单个任务完成情况，体验下降。

**理由**：`transient=True` 设计目的就是避免进度条残留；任务结果作为持久性提示，应在进度条清除后输出。

### 9.5 使用 MaxColumnsLayout 替代 DynamicColumns

**选定方案**：用 `MaxColumnsLayout` 替换旧版 `DynamicColumns`，按固定最大列数平均分配宽度。

**被否决的替代方案**：

- **在 `cx_wealthy` 中实现真正的动态列测量**：复杂度被低估，且 media_killer 当前场景不需要基于内容的动态列宽。
- **保留 `DynamicColumns` 名称但行为不变**：名实不符，`DynamicColumns` 暗示动态测量，会误导使用方。

**理由**：`MaxColumnsLayout` 诚实命名，行为简单可预测；对展示 Preset 详情面板等场景已足够。

### 9.6 say 输出状态摘要，whisper 输出详细清单

**选定方案**：`say()` 只输出简洁状态摘要（数量、模式、结果），具体文件列表、详细参数、原始 FFmpeg 输出等全部通过 `whisper()` 输出（仅 debug 可见）。

**被否决的替代方案**：

- **文件清单也用 `say()` 输出**：会让正常用户的终端被大量路径刷屏，与旧版实际行为不符。
- **所有信息都走 `say()`，不分层**：丢失 debug 模式的价值，正常用户和开发者看到同样的冗长输出。
- **用 `-v/--verbose` 单独开关详细输出**：`IAppEnvironment` 已经提供 `whisper()`/`debug_mode`，再引入新的 verbose 开关会增加概念数量。

**理由**：`IAppEnvironment` 的两级输出模型就是为这种场景设计的；`-d` 是已经存在的调试开关，无需新增概念。

### 9.7 保留 Mission 标识行的多色设计

**选定方案**：保留旧版多色标识行设计，但全部通过主题字段表达：`[cx.mk.mission.type]M[/] [cx.mk.mission.metadata][preset:inputs->outputs][/] [cx.mk.mission.name]name[/] [cx.success]完成[/]`。用于进度条描述和任务完成提示。

**被否决的替代方案**：

- **整行单一语义样式**：丢失通过颜色快速区分任务身份、状态和文件名的能力。
- **完全移除 `M` 标识和计数器**：多任务并发时用户难以追踪当前是哪条任务。
- **继续硬编码具体颜色**：违反新版"所有颜色必须走主题字段"的原则，无法通过主题覆盖。
- **将标识行全部映射到 `cx_wealthy` 通用字段**：`M`、JobCounter、元数据括号、文件名等没有对应通用字段，强行映射会降低设计质量。

**理由**：旧版的多色标识行是经过验证的 UX 设计，新版通过 `cx.mk.*` 字段保留其视觉结构，同时让所有颜色都可通过主题覆盖。

---

## 10. 下一步检查项

在开始实现前，确认以下事项：

1. [ ] 所有 `from cx_wealth` 的 import 已移除。
2. [ ] 已创建 `media_killer.theme` 模块并定义 `MEDIA_KILLER_STYLES`（`cx.mk.*`）。
3. [ ] `AppEnv.console` 已合并注入 `cx_wealthy.default_theme` + `MEDIA_KILLER_STYLES`。
4. [ ] `Progress` 已设置 `transient=True` 并共用 `AppEnv.console`。
5. [ ] `Mission` 已实现 `__rich_label__`（通过 mixin 或手动），全部使用 `cx.mk.*` 字段。
6. [ ] `Mission` 已实现 `__rich_detail__`（通过 mixin 或手动）。
7. [ ] 用户提示文本优先使用 `cx.*` 语义样式；media_killer 特有视觉角色使用 `cx.mk.*`。
8. [ ] 代码中无 `[red]`、`[blue]`、`[yellow]` 等硬编码具体颜色，全部走主题字段。
9. [ ] Mission 结果行在进度条消失后输出。
10. [ ] `say()` 只输出状态摘要，文件清单 / 详细参数 / FFmpeg 原始输出等沉入 `whisper()`。
11. [ ] `whisper()` 仅用于 debug 信息，不承载必须可见的用户提示。
