"""Jpegger 包入口。

该包提供 `run()` 函数作为 `[project.scripts]` 中 `jpegger` 命令的
入口点，负责安装 Rich 异常追踪并启动 `JpeggerApp`。
"""

from .simple_application import JpeggerApp


def run() -> None:
    """启动 Jpegger 命令行工具。"""
    from rich.traceback import install

    _ = install(show_locals=False, word_wrap=True, suppress=["rich"])
    with JpeggerApp() as app:
        app.run()
