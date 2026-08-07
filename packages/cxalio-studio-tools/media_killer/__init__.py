"""media_killer — 媒体文件批量转码工具。

CLI 入口：mediakiller = "media_killer:run"
"""

__version__ = "0.9.3"

import sys

from .appcontext import MediaKillerContext
from .appenv import appenv
from .application import MediaKillerApp


def run() -> None:
    """media_killer CLI 入口。"""
    from rich.traceback import install

    install(show_locals=False, word_wrap=True, suppress=["rich"])

    context = MediaKillerContext.from_arguments(sys.argv[1:])
    with appenv:
        with MediaKillerApp(
            appenv=appenv, context=context, progress=appenv.progress
        ) as app:
            app.run()


__all__ = ["MediaKillerApp", "run"]
