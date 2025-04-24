from collections.abc import Iterable, Sequence
import sys
from cx_studio.ffmpeg import FFmpeg
from cx_tools.app import IApplication, SafeError
from cx_wealth.indexed_list_panel import IndexedListPanel
from .appenv import appenv
from pathlib import Path


class FFPrettyApp(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments)
        self.arguments = []
        for a in self.sys_arguments:
            if a == "-d":
                appenv.debug_mode = True
            elif a == "--debug":
                appenv.debug_mode = True
            else:
                self.arguments.append(a)

        self.ffmpeg: FFmpeg = FFmpeg(appenv.ffmpeg_executable)

    def start(self):
        appenv.start()

    def stop(self):
        appenv.stop()

    def __exit__(self, exc_type, exc_val, exc_tb):
        result = False
        if exc_type is None:
            pass
        elif issubclass(exc_type, SafeError):
            appenv.say(exc_val)
            result = True
        self.stop()
        return result

    def input_files(self) -> Iterable[str]:
        input_marked = False
        for a in self.arguments:
            if a == "-i":
                input_marked = True
            elif input_marked:
                yield a
                input_marked = False

    def output_files(self) -> Iterable[str]:
        has_key = False
        for a in self.arguments:
            if a.startswith("-"):
                has_key = True
            else:
                if not has_key:
                    yield a
                else:
                    has_key = False

    def run(self):
        if not self.arguments:
            raise SafeError("No arguments provided.")

        if not appenv.ffmpeg_executable:
            raise SafeError("No ffmpeg executable found.")

        appenv.whisper("检查输入输出……")
        inputs = list(self.input_files())
        outputs = list(self.output_files())
        appenv.whisper(
            IndexedListPanel(inputs, title="输入文件"),
            IndexedListPanel(outputs, title="输出文件"),
        )

        # if not inputs:
        #     raise SafeError("No input files provided.")

        # if not outputs:
        #     raise SafeError("No output files provided.")

        # for i in inputs:
        #     if not Path(i).exists():
        #         raise SafeError(f"输入文件 {i} 不存在。")

        # non_exist_dirs = filter(
        #     lambda x: not x.exists(), [Path(a).parent for a in outputs]
        # )
        # if non_exist_dirs:
        #     for d in non_exist_dirs:
        #         d.mkdir(parents=True, exist_ok=True)
        #     appenv.whisper(IndexedListPanel(non_exist_dirs, title="创建的输出目录"))

        self.ffmpeg.execute(self.arguments)
