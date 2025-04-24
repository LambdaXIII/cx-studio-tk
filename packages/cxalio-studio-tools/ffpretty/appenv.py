from typing import override
from cx_tools_common.app_interface import IAppEnvironment
from cx_studio.path_expander import CmdFinder


class AppEnv(IAppEnvironment):
    def __init__(self):
        super().__init__()
        self.app_name = "FFpretty"
        self.app_version = "0.1"
        self.ffmpeg_executable = CmdFinder.which("ffmpeg")
        self.debug_mode = False

    @override
    def is_debug_mode_on(self):
        return self.debug_mode

    def start(self):
        self.whisper("FFpretty started")
        self.whisper(f"FFmpeg executable: {self.ffmpeg_executable}")

    def stop(self):
        self.whisper("FFpretty stopped")


appenv = AppEnv()
