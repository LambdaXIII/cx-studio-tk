import signal
from typing import override

from cx_studio.filesystem.path_expander import CmdFinder
from cx_studio.tui.tools.double_trigger import FIRST_TRIGGERED, SECOND_TRIGGERED
from cx_tools.app import IAppEnvironment
from cx_wealthy import rich_types as r
from rich.theme import Theme

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


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.console.push_theme(Theme(FFPRETTY_STYLES))
        self.app_name = "FFpretty"
        self.app_version = "0.8.7"
        self.ffmpeg_executable = CmdFinder.which("ffmpeg")
        self.debug_mode = False

        self.progress = r.Progress(
            # RenderableColumn("[bright_black]M[/]"),
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
            self.say("[cx.info]再次按下 Ctrl+C 确认退出[/]")

        @self.interrupt_handler.on(SECOND_TRIGGERED)
        def __when_really_wanna_quit():
            self.say("[cx.error]正在强制中断程序……[/]")

    @override
    def is_debug_mode_on(self):
        return self.debug_mode

    def start(self):
        self.whisper("FFpretty started")
        self.whisper(f"FFmpeg executable: {self.ffmpeg_executable}")
        self.progress.start()

    def stop(self):
        self.whisper("FFpretty stopped")
        self.progress.stop()


appenv = AppEnv()


signal.signal(signal.SIGINT, appenv.handle_interrupt)
