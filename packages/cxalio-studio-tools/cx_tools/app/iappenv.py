import asyncio
from abc import ABC
from typing import Self

from rich.console import Console
from rich.highlighter import RegexHighlighter

from cx_tools.i18n import _
from cx_wealthy import default_theme as cx_default_theme
from cx_studio import system
from cx_studio.tui import DoubleTrigger


class CxHighlighter(RegexHighlighter):
    """项目统一的 Rich 高亮器，为常见文本模式附加样式。

    匹配规则：
    - 括号括起的内容
    - 引号引用的字符串
    - 文件路径（Windows 和 Unix）
    - 数字
    - 命令行参数（--xxx 或 -x）

    高亮器在 Console 初始化时安装，但默认关闭（highlight=False）。
    仅在 `say()` 方法中开启，避免干扰不需要高亮的输出。
    """

    base_style = "cx."
    highlights = [
        r"(?P<brackets>\(.*?\))",  # 括号括起的
        r"(?P<quotes>\".*?\"|\'.*?\')",  # 引号引用的
        r"(?P<filepath>[A-Za-z]:[\\/][^:*?\"<>|\n]*)",  # Windows 文件路径
        r"(?P<filepath>[\\/][^:*?\"<>|\n]*)",  # Unix 文件路径
        r"(?P<number>\d+(?:\.\d+)?)",  # 数字
        r"(?P<argument>\b--?[a-zA-Z0-9_\-]+\b)",  # 命令行参数
    ]


class IAppEnvironment(ABC):
    """应用环境抽象基类。

    职责：
    - 提供统一的 Rich Console 实例（stderr 通道，带 CxHighlighter）
    - 定义 say()（始终显示）和 whisper()（仅 debug）两个输出层级
    - 管理应用生命周期：start() → run → stop()
    - 提供 DoubleTrigger 中断信号处理机制

    输出通道设计：
    Console 初始化为 stderr=True，因此 say() 和 whisper() 均走 stderr。
    stdout 保留给用户可能通过管道重定向的数据内容（使用内置 print()）。
    参见 cxalio-studio-tools/AGENTS.md「输出通道」章节。

    生命周期：
    with IAppEnvironment() as env:
        env.run(...)
    ── 进入时调用 start()，退出时调用 stop()。

    子类覆盖约定：
    - start() 中先调用 super().start()，再启动本工具特有的资源（如 Progress）。
    - stop() 中先清理本工具资源，再调用 super().stop()。
    - 若需覆盖 __exit__，必须保持 super().__exit__() 优先执行的结构。
      这是因为 appenv.stop() 幂等，先执行正常清理不会带来副作用，
      但跳过则可能导致 cleanup 遗漏。
    """

    def __init__(self) -> None:
        self.app_name = ""
        self.app_version = ""

        self.highlighter = CxHighlighter()
        self.console_theme = cx_default_theme

        # Console 初始化为 stderr=True：所有提示性输出走 stderr，
        # stdout 空闲给数据管道。say() 中开启高亮，whisper() 和平常
        # 的 console.print() 默认不开启。
        self.console = Console(
            stderr=True,
            theme=self.console_theme,
            highlighter=self.highlighter,
            highlight=False,  # 默认关闭，仅在 say() 中启用
        )

        # 两级中断事件：首次 Ctrl+C → wanna_quit，再次 → really_quit。
        # 异步任务应在每次迭代中检查这两个事件，决定是否取消。
        # 同步工具可以在 __exit__ 中直接 catch KeyboardInterrupt。
        self.wanna_quit_event = asyncio.Event()
        self.really_wanna_quit_event = asyncio.Event()

        self.interrupt_handler = DoubleTrigger()

        @self.interrupt_handler.on("first_triggered")
        def __when_wanna_quit():
            self.whisper(f"[cx.error]{_('触发中断信号…')}[/]")
            self.wanna_quit_event.set()

        @self.interrupt_handler.on("second_triggered")
        def __when_really_wanna_quit():
            self.whisper(f"[cx.error]{_('检测到强制中断信号…')}[/]")
            self.really_wanna_quit_event.set()

    def handle_interrupt(self, _sig, _frame) -> None:
        """SIGINT 处理器入口。触发 DoubleTrigger 的下一级。

        需在子模块末尾注册：signal.signal(signal.SIGINT, appenv.handle_interrupt)
        如果工具选择在 __exit__ 中 catch KeyboardInterrupt，则不注册此处理器。
        """
        self.interrupt_handler.trigger()

    def is_debug_mode_on(self) -> bool:
        """返回是否处于 debug 模式。子类应覆盖此方法返回真实状态。

        whisper() 的输出依赖此方法——仅在其返回 True 时输出。
        """
        return False

    def start(self) -> None:
        """应用环境启动。在 __enter__ 时调用。

        子类覆盖时应在开头调用 super().start()，再启动本工具特有资源。
        """
        self.whisper(f"{self.app_name} v{self.app_version} environment started.")

    def stop(self) -> None:
        """应用环境停止。在 __exit__ 时调用。

        子类覆盖时应在末尾调用 super().stop()。
        appenv.stop() 幂等，多次调用无害（Progress.stop() 可重复调用）。
        """
        self.whisper(f"{self.app_name} v{self.app_version} environment stopped.")

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        self.stop()
        self.whisper("Bye ~")
        return False

    def say(self, *args, **kwargs):
        """始终显示的用户提示。输出走 stderr（Console 初始化时 stderr=True）。

        强制开启高亮器（highlight=True），CxHighlighter 会按正则匹配
        文件路径、数字、命令行参数等并附加样式。

        注意：
        - 如需避免高亮器干扰（如 ASCII art），将内容包裹在
          r.Text(style=...) 中——显式 style 的 Text 对象不受高亮器影响。
        - 数据类输出（用户需要 | 管道获取的内容）不使用 say()，
          直接使用内置 print() 走 stdout。
        """
        kwargs["highlight"] = True
        self.console.print(*args, **kwargs)

    def whisper(self, *args, **kwargs):
        """仅 debug 模式下显示的非关键输出。走 stderr。

        仅在 is_debug_mode_on() 返回 True 时输出。
        样式固定为 dim，不开启高亮（highlight=False）。
        适合内部诊断信息、次要细节、开发日志。
        """
        if self.is_debug_mode_on():
            kwargs["style"] = "dim"
            kwargs["highlight"] = False
            self.console.print(*args, **kwargs)

    @staticmethod
    def is_user_admin() -> bool:
        """检查当前进程是否以管理员/root 权限运行。"""
        return system.is_user_admin()
