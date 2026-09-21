# cx-tools Specification

## Purpose
定义 cxalio-studio-tools 共享框架 `cx_tools.app` 的现行行为契约：三层分层架构、Application 编排器的构造注入与生命周期驱动、IAppContext 上下文管理器协议、IAppEnvironment 输出与中断职责、IAppComponent 组件基类契约、Progress 的职责边界，以及工具内部分层的组合面约束。

## Requirements

### Requirement: Application 通过构造参数接收 appenv 和 context

Application（`IApplication`）的 `__init__` MUST 接受 `appenv: IAppEnvironment` 和 `context: IAppContext` 两个构造参数，通过构造注入获取依赖。Application MUST NOT 从模块级全局单例导入 appenv。依赖组装职责属于工具入口代码（`__init__.py` 的 `run()`），入口代码 MUST 负责创建 appenv 和 context 实例并传入 Application 构造函数。模块级 appenv 单例仅可作为 signal handler 注册的载体保留，但 Application 和子组件 MUST NOT 导入使用该单例。

#### Scenario: 入口代码组装依赖

- **WHEN** 工具入口 `run()` 执行
- **THEN** 先创建 `<Tool>Context` 和 `<Tool>Env` 实例，再以 `appenv` 和 `context` 构造参数创建 Application 实例，不从模块级导入 appenv

#### Scenario: Application 不绑定特定 appenv

- **WHEN** 不同工具的入口代码传入各自的 `<Tool>Env` 实例
- **THEN** 同一个 Application 基类可被不同工具复用，不与特定 appenv 实例绑定

### Requirement: IAppContext 实现上下文管理器协议管理运行时资源

`IAppContext` MUST 实现上下文管理器协议（`__enter__` / `__exit__`）。`__enter__` 调用 `start()` 执行惰性初始化（如临时目录创建），`__exit__` 调用 `stop()` 执行确定性清理。`cleanup()` 方法 MUST 作为 `stop()` 的别名，支持非上下文管理器场景下的手动清理。`stop()` MUST 幂等——多次调用无害。`IAppContext` MUST 提供惰性 `temp_dir` 属性：首次访问时创建 `TemporaryDirectory`，`stop()` 时清理。子类覆盖 `start()` 时 MUST 先调用 `super().start()`，覆盖 `stop()` 时 MUST 先清理工具特定资源再调用 `super().stop()`。

#### Scenario: 异常路径下的确定性清理

- **WHEN** Application 在 `__enter__` 中启动 context 后 `start()` 抛出异常
- **THEN** MUST 调用 `context.__exit__()` 清理已分配资源（如临时目录），不泄漏

#### Scenario: stop 的幂等性

- **WHEN** 对已调用过 `stop()` 的 context 再次调用 `stop()`
- **THEN** 不报错、不重复清理已释放的资源

#### Scenario: temp_dir 惰性创建

- **WHEN** context 的 `__enter__` 尚未调用时访问 `temp_dir` 属性
- **THEN** 立即创建临时目录并返回其路径；后续 `stop()` 时自动清理

### Requirement: Application 驱动 context 生命周期

Application 的 `__enter__` MUST 调用 `context.__enter__()` 启动 context，`__exit__` MUST 先调用 `stop()`（工具特定清理），再调用 `context.__exit__()`（资源清理），且无论 `stop()` 是否抛异常都 MUST 执行 `context.__exit__()`（使用 try/finally）。Application 的 `__exit__` MUST 返回 `False`（不抑制异常），子类覆盖时 MUST 先调用 `super().__exit__()` 再处理特定异常。

#### Scenario: 正常生命周期

- **WHEN** 以 `with Application(appenv, context) as app:` 进入应用上下文
- **THEN** context 的 `start()` 被调用，`app.run()` 可正常执行；退出时 `stop()` 和 `context.__exit__()` 依次执行

#### Scenario: 子类 __exit__ 必须调用 super

- **WHEN** Application 子类覆盖 `__exit__` 处理 `KeyboardInterrupt`
- **THEN** MUST 先调用 `super().__exit__()` 确保 context 清理执行，再根据异常类型决定是否返回 `True` 抑制传播

#### Scenario: start 异常时 context 被清理

- **WHEN** Application 的 `start()` 方法抛出异常
- **THEN** MUST 调用 `context.__exit__()` 清理 context 资源，异常继续传播

### Requirement: appenv 上下文在 Application 外部管理

appenv 的生命周期 MUST 由工具入口代码在 Application 外部管理——入口代码 MUST 先进入 `with appenv:` 上下文，再进入 `with Application(...)` 上下文。Application MUST NOT 负责 appenv 的启动或停止。退出时 MUST 先退出 Application 上下文，再退出 appenv 上下文。

#### Scenario: 嵌套上下文顺序

- **WHEN** 工具入口执行 `with appenv:` 嵌套 `with Application(appenv, context):`
- **THEN** Application 退出时 context 被清理，appenv 仍在运行；appenv 上下文退出时执行 appenv 的 `stop()`

### Requirement: IAppEnvironment 提供分级输出与中断处理

`IAppEnvironment` MUST 提供 `say()`（始终显示）和 `whisper()`（仅 debug 模式显示）两个输出方法，两者 MUST 走 stderr（`Console(stderr=True)`）。MUST NOT 假设具体的 Live 组件类型——IAppEnvironment 不持有 Progress 引用。`IAppEnvironment` MUST 实现上下文管理器协议，`__enter__` 调用 `start()`、`__exit__` 调用 `stop()`。MUST 内置 `DoubleTrigger` 中断处理器，支持注册 `first_triggered` / `second_triggered` 回调。`set_debug_mode()` MUST 控制 whisper 的可见性。MUST NOT 被 Application 绑定为单例——模块级单例仅作为 signal handler 注册的载体保留，Application 与子组件 MUST NOT 导入使用。

#### Scenario: say 始终显示、whisper 仅 debug 模式

- **WHEN** debug 模式关闭时调用 `appenv.say("msg")` 和 `appenv.whisper("detail")`
- **THEN** `say()` 的输出出现在 stderr，`whisper()` 的输出不出现

#### Scenario: progress 不在通用接口中

- **WHEN** 工具需要进度条
- **THEN** MUST 由具体 `<Tool>Env` 子类创建 Progress（`console=self.console`），Application 从 `appenv.progress` 获取；IAppEnvironment 和 IApplication 接口 MUST NOT 定义 Progress 参数或属性

### Requirement: IAppComponent 作为签名契约不存储依赖

`IAppComponent.__init__` MUST 接受可选参数 `appenv: IAppEnvironment | None` 和 `context: IAppContext | None`，仅作为签名契约提示，MUST NOT 在基类中存储或暴露这些参数（基类 `__init__` 体为空操作）。子类 MUST 在各自的 `__init__` 中调用 `super().__init__(appenv, context)` 后自行赋值 `self.appenv = appenv` 和 `self.context = context`，使类型从子类参数声明推断而非被基类收窄。

#### Scenario: 子类类型推断

- **WHEN** `MediaScoutContext` 子类接收 `context: MediaScoutContext` 参数并自行赋值
- **THEN** `self.context` 的类型推断为 `MediaScoutContext`（具体子类），不被基类 property 收窄为 `IAppContext`

### Requirement: 子组件透明接收依赖不持有 parent 引用

CLI 特化组件 MUST 按需接收 `context` / `appenv` / `progress` 作为构造参数，MUST NOT 接收 `parent: SomeApplication` 引用。组件只接收它需要的依赖——仅需 `appenv`（不需要 context）的组件 MUST 接收 `env: IAppEnvironment` 参数而非继承 `IAppComponent`。不需要 appenv 或 context 的组件 MUST NOT 继承 `IAppComponent`，保持为通用功能组件。

#### Scenario: 按需接收最小依赖集

- **WHEN** 某组件只需要 `appenv.say()` 输出能力
- **THEN** 该组件接收 `env: IAppEnvironment` 参数，不继承 IAppComponent，不接收 context

#### Scenario: 可独立测试

- **WHEN** 对某 CLI 特化组件编写单元测试
- **THEN** 可独立构造 mock context 和 mock appenv 传入组件构造函数，无需创建完整 Application 实例

### Requirement: CLI 特化组件与通用功能组件分层

CLI 工具中的所有类 MUST 按是否依赖运行环境分为两层：继承 `IAppComponent` 的 CLI 特化组件（需要 appenv 或 context），与不继承 `IAppComponent` 的通用功能组件（纯算法、IO、值对象、数据处理）。新组件如果需要调用 `appenv.say()` / `appenv.whisper()` 或读取 `context` 字段 MUST 继承 `IAppComponent`；如果只做算法/IO/数据处理 MUST NOT 继承 `IAppComponent`。

#### Scenario: 判定边界清晰

- **WHEN** 新增一个需要调用 `appenv.say()` 输出结果的组件
- **THEN** 该组件 MUST 继承 `IAppComponent` 并通过构造参数接收 appenv

#### Scenario: 通用组件不依赖运行环境

- **WHEN** 新增一个纯数据处理的过滤器类
- **THEN** 该类 MUST NOT 继承 `IAppComponent`、MUST NOT 导入 appenv 或 context

### Requirement: 工具内部分层 common 与 components 的组合面约束

每个 CLI 工具包内部分为 `common/`（不需要 appenv 的非耦合能力）与 `components/`（需要 appenv 或含工具特定逻辑）两层。判别标准为 appenv 依赖加特化与否：不依赖 appenv 且非工具特定的放 `common/`，否则放 `components/`。公共能力 MUST 在设计之初规划，MUST NOT 事后从 `components` 反向抽取。工具间 import 只允许指向 `package.common`（可到子包层级），MUST NOT 导入其他工具的 `components/`。

#### Scenario: 工具间组合通过 common

- **WHEN** media_killer 需要使用 ffpretty 的任务执行能力
- **THEN** 导入路径指向 `ffpretty.common.executor`，不导入 `ffpretty.components` 下的任何模块

#### Scenario: 无 common 工具不强制区分

- **WHEN** 某工具（如 hosts_keeper）所有组件都依赖 appenv
- **THEN** 不强制区分 common/components，不为凑 common 而强行抽取

### Requirement: ConfigManager 管理配置与日志目录

`ConfigManager` MUST 根据 `app_name` 确定配置目录（`~/.config/cx-studio/<app_name>/`）和日志目录（配置目录下 `logs/`）。`new_log_file()` MUST 创建带时间戳和随机字符串的日志文件。`remove_old_log_files(keep)` MUST 按修改时间排序，仅保留最新的 `keep` 个日志文件。

#### Scenario: 配置目录定位

- **WHEN** 以 `app_name="media_scout"` 创建 ConfigManager
- **THEN** `config_dir` 为 `~/.config/cx-studio/media_scout/`
