from typing import override
from cx_tools.app import IAppEnvironment
from cx_studio.path_expander import CmdFinder
from cx_wealth import rich_types as r
import signal


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "FFpretty"
        self.app_version = "0.5.1.5"
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
