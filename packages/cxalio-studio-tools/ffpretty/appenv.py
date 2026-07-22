import signal
from typing import TYPE_CHECKING, override

from . import __version__

from cx_studio.filesystem.path_expander import CmdFinder
from cx_studio.clikit import FIRST_TRIGGERED, SECOND_TRIGGERED
from cx_tools.app import IAppEnvironment
from cx_tools.app.config_manager import ConfigManager
from cx_wealthy import rich_types as r
from media_killer.media import MediaDB
from rich.theme import Theme

if TYPE_CHECKING:
    from .mission_runner import MissionRunner

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
        self.app_version = __version__
        self.debug_mode = False

        # 复用 media_killer 的配置空间，共享探测缓存
        self.config_manager = ConfigManager("MediaKiller")
        result = CmdFinder.which("ffmpeg")
        self._ffmpeg_executable = str(result) if result else None
        self.media_db = MediaDB(db_path=self.config_manager.get_file("media_info.db"))

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

        self._active_runner: MissionRunner | None = None

        @self.interrupt_handler.on(FIRST_TRIGGERED)
        def __when_wanna_quit():
            self.say("[cx.info]再次按下 Ctrl+C 确认退出[/]")

        @self.interrupt_handler.on(SECOND_TRIGGERED)
        def __when_really_wanna_quit():
            self.say("[cx.error]正在强制中断程序……[/]")
            if self._active_runner is not None:
                self._active_runner.cancel()

    @property
    def ffmpeg_executable(self) -> str | None:
        """ffmpeg 可执行文件路径（在 __init__ 中缓存的惰性扫描结果）。"""
        return self._ffmpeg_executable

    @override
    def is_debug_mode_on(self):
        return self.debug_mode

    def start(self):
        self.whisper("FFpretty started")
        self.whisper(f"FFmpeg executable: {self.ffmpeg_executable}")
        self.media_db.connect()
        self.progress.start()

    def stop(self):
        self.media_db.close()
        self.whisper("FFpretty stopped")
        self.progress.stop()


appenv = AppEnv()
signal.signal(signal.SIGINT, appenv.handle_interrupt)
