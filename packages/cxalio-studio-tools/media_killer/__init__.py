"""media_killer — 媒体文件批量转码工具。

CLI 入口：mediakiller = "media_killer:run"
"""

__version__ = "0.9.2"

from .application import Application


def run() -> None:
    """media_killer CLI 入口。"""
    from rich.traceback import install

    install(show_locals=False, word_wrap=True, suppress=["rich"])

    with Application() as app:
        app.run()


__all__ = ["Application", "run"]
