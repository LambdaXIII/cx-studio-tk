import asyncio
from abc import ABC, abstractmethod

from rich.console import Console

from cx_studio.utils.tools import DoubleTrigger
import cx_wealth.rich_types as r
from typing import Union

from rich.highlighter import RegexHighlighter

DEFAULT_STYLES = {
    "cx.info": "blue",
    "cx.debug": "bright_black",
    "cx.warning": "yellow",
    "cx.error": "red",
    "cx.argument": "bold green1",
    "cx.success": "green1",
    "cx.whisper": "dim",
    "cx.number": "yellow",
    "cx.brackets": "magenta",
    "cx.quotes": "light_pink1",
    "cx.filepath": "bold cyan underline",
}
cx_default_theme = r.Theme(DEFAULT_STYLES)


class CxHighlighter(RegexHighlighter):
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

    def __init__(self):
        self.app_name = ""
        self.app_version = ""
        self.highlighter = CxHighlighter()
        self.console_theme = cx_default_theme
        self.console = Console(
            stderr=True,
            theme=self.console_theme,
            highlighter=self.highlighter,  # 全局安装默认的Highlighter
            highlight=False,  # 屏蔽默认的Highlighter，将只在 say 方法中启用
        )

        self.wanna_quit_event = asyncio.Event()
        self.really_wanna_quit_event = asyncio.Event()

        self.interrupt_handler = DoubleTrigger()

        @self.interrupt_handler.on("first_triggered")
        def __when_wanna_quit():
            self.whisper("[cx.error]触发中断信号…[/]")
            # self.wanna_quit = True
            self.wanna_quit_event.set()

        @self.interrupt_handler.on("second_triggered")
        def __when_really_wanna_quit():
            self.whisper("[cx.error]检测到强制中断信号…[/]")
            # self.really_wanna_quit = True
            self.really_wanna_quit_event.set()

    def handle_interrupt(self, _sig, _frame):
        self.interrupt_handler.trigger()

    # @abstractmethod
    def is_debug_mode_on(self):
        return False

    # @abstractmethod
    def start(self):
        self.whisper(
            "{} v{} environment started.".format(self.app_name, self.app_version)
        )

    # @abstractmethod
    def stop(self):
        self.whisper(
            "{} v{} environment stopped.".format(self.app_name, self.app_version)
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.whisper("Bye ~")
        return False

    def say(self, *args, **kwargs):
        # highlighted_args = (
        #     self.highlighter(x) if isinstance(x, Union[str, r.Text]) else x
        #     for x in args
        # )
        kwargs["highlight"] = True
        self.console.print(*args, **kwargs)

    def whisper(self, *args, **kwargs):
        if self.is_debug_mode_on():
            # highlighted_args = (self.highlighter(x) or x for x in args)
            kwargs["style"] = "dim"
            kwargs["highlight"] = False
            self.console.print(*args, **kwargs)
