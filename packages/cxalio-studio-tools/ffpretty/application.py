from collections.abc import Iterable
from cx_studio.ffmpeg import FFmpeg
from cx_tools_common.app_interface import IApplication, SafeError
from .appenv import appenv


class FFPrettyApp(IApplication):
    def __init__(self, arguments: Iterable[str]):
        super().__init__()
        self.arguments = []
        for a in arguments:
            if a == "-d":
                appenv.debug_mode = True
            elif a == "--debug":
                appenv.debug_mode = True
            else:
                self.arguments.append(a)

        self.ffmpeg: FFmpeg

    def start(self):
        appenv.start()

    def stop(self):
        appenv.stop()

    def __exit__(self, exc_type, exc_val, exc_tb):
        result = super().__exit__(exc_type, exc_val, exc_tb)
        return result

    def run(self):
        if not self.arguments:
            raise SafeError("No arguments provided.")

        if not appenv.ffmpeg_executable:
            raise SafeError("No ffmpeg executable found.")

        self.ffmpeg = FFmpeg(appenv.ffmpeg_executable)
