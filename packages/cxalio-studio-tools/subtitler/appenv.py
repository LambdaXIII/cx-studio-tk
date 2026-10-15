"""Subtitler 全局应用环境。

`SubtitlerEnv` 继承 `IAppEnvironment`，提供 Rich 控制台、debug 输出门控，
并在启动时居中展示 ASCII 横幅与版本行。
"""

import importlib.resources
from typing import override

from cx_tools.app import IAppEnvironment
from cx_wealthy import rich_types as r

from . import __version__


class SubtitlerEnv(IAppEnvironment):
    """Subtitler 应用环境实例。"""

    app_name: str
    app_version: str

    def __init__(self) -> None:
        """初始化环境，绑定应用名与版本号。"""
        super().__init__()
        self.app_name = "Subtitler"
        self.app_version = __version__

    @override
    def start(self) -> None:
        """启动环境：先展示横幅，再执行基类启动。"""
        self.show_banner()
        super().start()

    @override
    def stop(self) -> None:
        """停止环境。无工具特有资源需清理。"""
        super().stop()

    def show_banner(self) -> None:
        """居中展示 ASCII 横幅与版本行。"""
        assert __package__ is not None, "SubtitlerEnv 必须作为包的一部分被导入"
        banner_text = importlib.resources.read_text(
            __package__, "banner.txt", encoding="utf-8"
        )
        banners = [
            r.Align.center(
                r.Text(banner_text, style="bold cyan", no_wrap=True, overflow="crop")
            ),
            r.Align.center(r.Text(f"v{self.app_version}", style="bold cyan")),
        ]
        self.say(r.Group(*banners))
