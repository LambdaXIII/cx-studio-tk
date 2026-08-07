"""Jpegger 包入口。

该包提供 `run()` 函数作为 `[project.scripts]` 中 `jpegger` 命令的
入口点，负责安装 Rich 异常追踪并启动 `JpeggerApp`。
"""

__version__ = "0.8.4"

import sys

from cx_tools.app import SafeError

from .application import JpeggerApp
from .appcontext import JpeggerContext
from .appenv import appenv


def run() -> None:
    """启动 Jpegger 命令行工具。"""
    from rich.traceback import install

    _ = install(show_locals=False, word_wrap=True, suppress=["rich"])
    try:
        context = JpeggerContext.from_arguments(sys.argv[1:])
    except SafeError as e:
        appenv.say(f"[{e.style}]{e}[/]")
        return
    with appenv:
        with JpeggerApp(appenv=appenv, context=context) as app:
            app.run()
