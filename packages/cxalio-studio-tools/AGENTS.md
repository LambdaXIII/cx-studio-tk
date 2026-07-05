# cxalio-studio-tools CLI 工具编写规范

本文件覆盖 `packages/cxalio-studio-tools/` 分发包内所有 CLI 工具及共享框架 `cx_tools` 的约定。不重复仓库根目录 `AGENTS.md` 中的内容（项目结构、依赖链、版本策略、i18n 流程等）。

---

## 输出通道

`IAppEnvironment.console` 初始化为 `stderr=True`，因此 `say()` 和 `whisper()` 的输出均走 **stderr**。stdout 保留给用户可能通过管道重定向的数据输出。

### 三者的选择

|函数|通道|何时使用|
|---|---|---|
|`appenv.say()`|stderr|始终显示的用户提示，如操作结果、错误信息、完成状态|
|`appenv.whisper()`|stderr|仅 debug 模式（`-d`）下显示，如内部诊断细节|
|内置 `print()`|stdout|用户需要 `|` 管道获取的数据内容，如 pretend 模式下的输出结果|

### 规则

- 所有用户可见的提示性文字必须使用 `say()` 或 `whisper()`。禁止裸 `console.print()` 调用（banner 例外，见下文）。
- 数据类输出（如"假装模式下显示将要写入的内容"）使用 `print()`，确保管道可用。
- `say()` 内部强制开启高亮器（`highlight=True`），会按正则匹配文件路径、数字、命令行参数等并附加样式。如需避免高亮器干扰（如 ASCII art），将内容包裹在 `r.Text(style=...)` 中——显式 style 的 Text 对象不受高亮器影响。

---

## Banner 显示

工具启动时显示 banner。推荐模式：

```
banner_text = importlib.resources.read_text(__package__, "banner.txt", ...)
banners.append(r.Align.center(r.Text(banner_text, style="bold cyan", no_wrap=True, overflow="crop")))
banners.append(r.Align.center(r.Text(_("标语"), style="bold cyan")))
self.say(r.Group(*banners))
```

要点：
- 每个元素用 `r.Text(style=...)` 包裹，赋予显式样式，阻止高亮器覆盖。
- 使用 `self.say()` 输出，保持输出通道统一。
- 不使用 `console.print(group, style=..., highlight=False)` 绕过 `say()`。

---

## Progress 与输出时序

Rich Progress 基于 Live display。Progress 活跃期间调用 `console.print()`（`say()` 内部使用）会导致终端渲染异常，在部分 Windows 终端上表现为 progress bar 残留副本。

### 约束

1. **`transient=True`**——所有 `Progress` 实例必须设为 `transient=True`。设置后 progress 在 `stop()` 时自动清屏，不滞留上次运行的状态。`transient=False` 仅在需要保留进度历史时有意义，未经讨论不得使用。

2. **`say()` 不在 progress 活跃期调用**——如果业务逻辑需要在进度完成后输出用户提示，必须先 `appenv.progress.stop()` 再 `say()`。progress 的 `stop()` 幂等，重复调用无害。

3. **警惕 generator 延迟执行**——若进度构建逻辑封装在返回 generator 的函数中，函数体在被迭代之前不会执行。以下顺序错误：

   ```
   gen = builder.build(profiles)  # generator，未执行
   appenv.progress.stop()          # 过早——实际工作还没开始
   for x in gen:                   # 实际执行在这里
   ```

   正确顺序：

   ```
   gen = builder.build(profiles)
   for x in gen:                   # 先耗尽 generator
       ...
   appenv.progress.stop()          # 再停 progress
   ```

---

## `__exit__` 覆盖模式

工具自定义 `__exit__` 必须遵循以下结构：

```python
@override
def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
    result = super().__exit__(exc_type, exc_val, exc_tb)  # 始终先走正常清理
    if exc_type is KeyboardInterrupt:                      # 按需处理具体异常
        appenv.stop()                                       # 幂等
        appenv.say(f"[cx.error]{_('用户中断')}[/]")
        result = True
    return result
```

要点：
- `super().__exit__()` 始终优先执行，确保 `appenv.stop()`（progress 清理、临时目录删除等）不因异常类型跳过。
- `appenv.stop()` 幂等，多次调用无害。
- 返回 `True` 抑制异常传播（用户提示已由 `say()` 输出），返回 `False` 或 `None` 则异常继续传播。

---

## 中断处理（两种策略）

### 策略 A：`__exit__` 中 catch KeyboardInterrupt

适用于不需要多次 Ctrl+C 取消流程的工具。在 `Application.__exit__` 中直接检查 `exc_type is KeyboardInterrupt`，无需注册 signal handler。见上方 `__exit__` 覆盖模式示例。

### 策略 B：DoubleTrigger 信号机制

`IAppEnvironment` 内置 `DoubleTrigger` 对象。在 `AppEnv.__init__` 中注册回调：

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

首次 Ctrl+C 触发 `first_triggered`（设置`wanna_quit_event`，提示用户再次确认）。再次 Ctrl+C 触发 `second_triggered`（设置 `really_quit_event`，强制中断）。适用于有长时间异步操作需要优雅取消的工具。

---

## 工具内的引用模式

### `appenv` 单例

每个工具的 `appenv.py` 末尾定义模块级单例：

```python
appenv = AppEnv()
```

其他模块从此模块导入：

```python
from .appenv import appenv
appenv.say(...)
appenv.whisper(...)
```

### i18n

所有翻译函数从 `cx_tools.i18n` 导入，不在工具间交叉导入：

```python
from cx_tools.i18n import _, _ng
```

### 框架导入

共享框架类从 `cx_tools.app` 导入：

```python
from cx_tools.app import IAppEnvironment, ConfigManager
```
