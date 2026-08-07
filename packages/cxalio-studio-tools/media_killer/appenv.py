"""media_killer 应用环境。

继承 IAppEnvironment，提供 media_killer 专用的运行环境：
- 合并自定义主题 (cx.mk.*)
- 初始化 Progress (transient=True)
- 注册 DoubleTrigger 中断回调
"""

from __future__ import annotations

from . import __version__

import signal

from cx_tools.app import IAppEnvironment
from media_killer.i18n import _
from cx_wealthy import rich_types as r

from .theme import media_killer_theme


class MediaKillerEnv(IAppEnvironment):
    """media_killer 应用环境。

    继承 IAppEnvironment，提供 media_killer 专用的运行环境：
    - 合并自定义主题 (cx.mk.*) 到 Console
    - 初始化 Progress (transient=True, 共用 console)
    - 注册 DoubleTrigger 中断回调

    Attributes:
        progress: Rich Progress 实例
    """

    def __init__(self) -> None:
        """初始化 MediaKillerEnv。

        设置应用元数据、合并自定义主题、初始化 Progress。
        """
        super().__init__()

        # 应用元数据
        self.app_name = "MediaKiller"
        self.app_version = __version__

        # 合并自定义主题
        self.console_theme = media_killer_theme
        self.console = r.Console(
            stderr=True,
            theme=self.console_theme,
            highlighter=self.highlighter,
            highlight=False,
        )

        # Progress 初始化（transient=True, 共用 console）
        self.progress = r.Progress(
            r.SpinnerColumn(),
            r.TextColumn(
                "[progress.description]{task.description}",
                table_column=r.Column(ratio=60, no_wrap=True),
            ),
            r.BarColumn(table_column=r.Column(ratio=40)),
            r.TaskProgressColumn(justify="right"),
            r.TimeRemainingColumn(compact=True),
            console=self.console,
            transient=True,
            expand=True,
        )

    def start(self) -> None:
        """启动应用环境。

        调用 super().start()，启动 Progress。
        """
        super().start()
        self.progress.start()

    def stop(self) -> None:
        """停止应用环境。

        停止 Progress，调用 super().stop()。
        """
        self.progress.stop()
        super().stop()


# 全局单例
appenv = MediaKillerEnv()

# 注册 SIGINT 处理器
signal.signal(signal.SIGINT, appenv.handle_interrupt)
