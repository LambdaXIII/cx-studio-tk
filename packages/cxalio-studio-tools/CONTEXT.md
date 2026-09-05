# cxalio-studio-tools

`packages/cxalio-studio-tools/` 是包含 6 个 CLI 工具（media_scout、media_killer、ffpretty、jpegger、hosts_keeper、cxnote）与共享框架 `cx_tools` 的分发包。所有工具均构建在 `cx_tools.app` 应用框架之上，共享统一的应用生命周期管理、Rich 输出与中断处理。根目录 `AGENTS.md` 中的全局规则优先；本文档仅补充本工作空间特有的规则。

## 架构

### 三层分层

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

### 层间依赖规则

- Application 依赖 appenv 和 context，通过构造参数注入
- 子组件透明接收 context/appenv/progress（按需），不接收 parent 引用
- appenv 和 context 互不依赖
- 基础设施层（cx_studio）不依赖任何 CLI 组件

### 组件分层

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

### 工具内部分层：common / components

工具包内部按能力归属分两层：

- **`common/`** — 不需要 appenv 的非耦合能力（对外提供面）。如 ffpretty.common（Mission/Executor/MediaDB）、media_killer.common（MissionHQ 调度层）、media_scout.common（inspectors）。
- **`components/`** — 需要 appenv 或含工具特定转化/包装逻辑的组件。如 ffpretty.components（mission_runner/mission_maker/info_elements）、media_killer.components（preset/expander/script_maker/mission_store）。

判别标准 = **appenv 依赖 + 特化与否**：不依赖 appenv 且非工具特定 → common；否则 → components。公共能力在设计之初规划（非消费者驱动），避免事后从 components 反向抽取。

**组合面契约**：工具间 import 只允许指向 `package.common`（可到 `package.common.subpackage`，如 `ffpretty.common.executor` 的事件常量）；ToolApp/ToolHelp 一级内容可从包根直接导入。不提供 common 的工具（hosts_keeper、jpegger）不强制区分 common/components。

## 工具编写模式

所有 CLI 工具遵循统一的编写模式，共享相同的应用生命周期和基础设施。

### CLI 入口点

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

### 参数解析

每个工具使用 `<Tool>Context` 类（`from_arguments()` 唯一工厂，`kwargs` 白名单赋值），不直接暴露 argparse。

### 帮助系统

每个工具使用 `WealthyHelp` DSL（`add_group`/`add_action`/`add_note` 声明式构建），帮助文件通过 `cx_studio.i18n.load_localized_text()` 加载（按 locale 自动选择 `help.md` / `help.<locale>.md`）。

### 异常体系

`SafeError`（可恢复应用异常，带 style）由 `Application.__exit__` 捕获。

### 分级输出

`IAppEnvironment` 提供 `say()`（始终显示）和 `whisper()`（仅 debug 模式）两个输出层级。详见下方"输出通道"。

### 输出通道

`IAppEnvironment.console` 初始化为 `stderr=True`，因此 `say()` 和 `whisper()` 的输出均走 **stderr**。stdout 保留给用户可能通过管道重定向的数据输出。

#### 三者的选择

| 函数               | 通道   | 何时使用                                                 |
| ------------------ | ------ | -------------------------------------------------------- |
| `appenv.say()`     | stderr | 始终显示的用户提示，如操作结果、错误信息、完成状态       |
| `appenv.whisper()` | stderr | 仅 debug 模式（`-d`）下显示，如内部诊断细节              |
| 内置 `print()`     | stdout | 用户需要管道获取的数据内容，如 pretend 模式下的输出结果 |

> 通常不直接使用 print 函数，而是在 appenv 中初始化一个新的 Console 负责 stdout 输出。

#### 规则

- 所有用户可见的提示性文字必须使用 `say()` 或 `whisper()`。禁止裸 `console.print()` 调用（banner 例外，见下文）。
- 数据类输出（如"假装模式下显示将要写入的内容"）使用 `print()`，确保管道可用。
- `say()` 内部强制开启高亮器（`highlight=True`），会按正则匹配文件路径、数字、命令行参数等并附加样式。如需避免高亮器干扰（如 ASCII art），将内容包裹在 `r.Text(style=...)` 中——显式 style 的 Text 对象不受高亮器影响。

## 应用环境与 UI

### Banner 显示

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

### Progress 与输出时序

Progress 用 `console=self.console` 创建。Rich Live 接管该 console 的输出——`self.console.print()`（基类 `say()`/`whisper()` 调用的方法）在 Live 运行期间会自动暂停 Live 渲染、输出文本、恢复 Live，无需手动 stop/start progress。`<Tool>Env` 子类不应 override `say()`/`whisper()` 来协调 progress。

#### 约束

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

### __exit__ 覆盖模式

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

### 中断处理

#### 策略 A：`__exit__` 中 catch KeyboardInterrupt

适用于不需要多次 Ctrl+C 取消流程的工具。在 `Application.__exit__` 中直接检查 `exc_type is KeyboardInterrupt`，无需注册 signal handler。见上方 `__exit__` 覆盖模式示例。

#### 策略 B：DoubleTrigger 信号机制

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

#### 策略选择原则

- 同步代码路径（如 hosts_keeper 的 for 循环）→ 策略 A（KeyboardInterrupt），不注册 signal handler
- 异步代码路径（如 media_killer 的 asyncio loop）→ 策略 B（DoubleTrigger + signal handler），但必须用手动 event loop（`run_async()`）而非 `asyncio.run()`，否则 Python 3.13 会覆盖 SIGINT handler

## 引用模式

### Application 组装

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

### appenv 单例

每个工具的 `appenv.py` 末尾仍定义模块级单例（用于 signal handler 注册）：

```python
appenv = <Tool>Env()
signal.signal(signal.SIGINT, appenv.handle_interrupt)
```

但 Application 和子组件不再通过 `from .appenv import appenv` 导入使用，而是通过构造参数接收。

### i18n

每个工具自持 `i18n/` 模块和 `i18n/locales/` 翻译文件，不允许交叉导入。各工具从自己的 `i18n` 模块导入翻译函数：

| 工具 | 导入 |
| --- | --- |
| cx_tools（框架） | `from cx_tools.i18n import _, _ng` |
| media_scout | `from media_scout.i18n import _, _ng` |
| media_killer | `from media_killer.i18n import _, _ng` |
| ffpretty | `from ffpretty.i18n import _, _ng` |
| jpegger | `from jpegger.i18n import _, _ng` |
| hosts_keeper | `from hosts_keeper.i18n import _, _ng` |

### 框架导入

共享框架类从 `cx_tools.app` 导入：

```python
from cx_tools.app import IAppEnvironment, ConfigManager
```

## CHANGELOG 编写

- CHANGELOG 中的版本号为**整个发布单元**（cxalio-studio-tools）的版本，不是某个工具的版本
- 一次迭代涉及多个工具时，可按工具分别组织编写（按标题分组）；也可以直接编写每个条目，并在每项中说清楚是在哪个包中进行的修改

## Language

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
CLI 工具，终端快速笔记（包 `cx_note`）——以域组织的待办便签：快记字符串条目、按域浏览、跟踪待办状态并自动清除超龄已完成条目。

**域**：
cx-note 的字面命名空间——形如 `/a/b` 的路径式字符串，仅用作条目归属的组织单位，与文件系统目录结构无绑定；身份判定大小写不敏感，存储保留首次出现的字面。
_Avoid_: 目录、文件夹（域不映射目录结构）

**根域**：
域树的顶层 `/`，对应 $HOME；`-g` 参数是它的快捷指定方式。

**条目**：
cx-note 记录的最小单元——字符串内容（可含换行）、三态状态、创建/完成日期、所属域与 4 位 ID。

**清除**：
将条目从存储中物理删除的动作（手动 `clear` 或超龄自动触发）；已完成只是状态标记，不等于清除，被清除的条目不可恢复。
_Avoid_: 归档

**清理**：
cx-note 对超龄已完成条目的自动维护——保存时顺带执行、仅限当前域、尽力而为不保证完备；未完成条目永不参与清理。与「清除」的区别：清除是用户发起的动作，清理是工具的维护行为。
