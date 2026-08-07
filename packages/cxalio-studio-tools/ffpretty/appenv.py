import signal
from typing import override

from cx_studio.clikit import FIRST_TRIGGERED, SECOND_TRIGGERED
from cx_tools.app import IAppEnvironment
from cx_wealthy import rich_types as r
from ffpretty.i18n import _

from . import __version__

FFPRETTY_STYLES: dict[str, str] = {
    "ffpretty.info.filename": "red",
    "ffpretty.info.format_name": "green",
    "ffpretty.info.codec_name": "green1",
    "ffpretty.info.format_long_name": "blue",
    "ffpretty.info.stream_label": "blue",
    "ffpretty.info.duration": "cyan",
    "ffpretty.info.bit_rate": "yellow",
    "ffpretty.info.file_size": "yellow",
    "ffpretty.info.border": "dim",
}


class FFPrettyEnv(IAppEnvironment):
    """FFPretty 应用环境。

    职责：console 输出、Progress 管理、中断处理、banner 显示。
    不持有业务状态（配置、MediaDB、ffmpeg 路径等已迁移到 FFPrettyContext/Application）。
    """

    def __init__(self):
        super().__init__()
        self.console.push_theme(r.Theme(FFPRETTY_STYLES))
        self.app_name = "FFpretty"
        self.app_version = __version__

        self.progress = r.Progress(
            r.SpinnerColumn(),
            r.TextColumn(
                "[progress.description]{task.description}",
                table_column=r.Column(ratio=60, no_wrap=True),
            ),
            r.BarColumn(table_column=r.Column(ratio=40)),
            r.TaskProgressColumn(justify="right"),
            r.TimeRemainingColumn(compact=True),
            expand=True,
            console=self.console,
            transient=True,
        )

        @self.interrupt_handler.on(FIRST_TRIGGERED)
        def __when_wanna_quit():
            self.say(f"[cx.info]{_('再次按下 Ctrl+C 确认退出')}[/]")

        @self.interrupt_handler.on(SECOND_TRIGGERED)
        def __when_really_wanna_quit():
            self.say(f"[cx.error]{_('正在强制中断程序……')}[/]")

    @override
    def start(self):
        """启动应用环境。"""
        super().start()
        self.progress.start()

    @override
    def stop(self):
        """停止应用环境。"""
        self.progress.stop()
        super().stop()


appenv = FFPrettyEnv()
signal.signal(signal.SIGINT, appenv.handle_interrupt)
