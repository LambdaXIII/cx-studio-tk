"""media_killer — 媒体文件批量转码工具。

CLI 入口：mediakiller = "media_killer:run"
"""

__version__ = "0.9.3"

import sys

from cx_tools.app import SafeError

from .appcontext import MediaKillerContext
from .appenv import appenv
from .application import MediaKillerApp


def run() -> None:
    """media_killer CLI 入口。"""
    from rich.traceback import install

    install(show_locals=False, word_wrap=True, suppress=["rich"])

    try:
        context = MediaKillerContext.from_arguments(sys.argv[1:])
    except SafeError as e:
        appenv.say(f"[{e.style}]{e}[/]")
        return
    with appenv:
        with MediaKillerApp(
            appenv=appenv, context=context, progress=appenv.progress
        ) as app:
            app.run()


__all__ = ["MediaKillerApp", "run"]
