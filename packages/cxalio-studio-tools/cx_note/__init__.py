"""cxnote 包入口。

该包提供 `run()` 函数作为 `[project.scripts]` 中 `cxnote` 命令的
入口点，负责安装 Rich 异常追踪并启动 `CxNoteApp`。
"""

__version__ = "1.1.1"

import sys

from cx_tools.app import SafeError

from .application import CxNoteApp
from .appcontext import CxNoteContext
from .appenv import appenv


def run() -> None:
    """启动 cxnote 命令行工具。"""
    from rich.traceback import install

    _ = install(show_locals=False, word_wrap=True, suppress=["rich"])
    try:
        context = CxNoteContext.from_arguments(sys.argv[1:])
    except SafeError as e:
        appenv.say(f"[{e.style}]{e}[/]")
        return
    with appenv:
        with CxNoteApp(appenv=appenv, context=context) as app:
            app.run()
