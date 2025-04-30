import asyncio
from collections.abc import Iterable, Sequence
from datetime import datetime
import itertools
import sys
from cx_studio.core.cx_time import CxTime
from cx_studio.ffmpeg import FFmpegAsync
from cx_studio.ffmpeg.cx_ff_infos import FFmpegCodingInfo
from cx_tools.app import IApplication, SafeError
from cx_wealth.indexed_list_panel import IndexedListPanel
from .appenv import appenv
from pathlib import Path
from cx_wealth import rich_types as r


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

        if "-y" not in self.arguments and "-n" not in self.arguments:
            self.arguments.append("-n")

        self.ffmpeg = FFmpegAsync(appenv.ffmpeg_executable)
        self.start_time: datetime

        self._task_description: str = ""

    def start(self):
        appenv.start()
        self.start_time = datetime.now()

    def stop(self):
        appenv.stop()
        time_span = datetime.now() - self.start_time
        if time_span.total_seconds() > 5:
            appenv.say(
                "[dim]用时 [blue]{}[/]。".format(
                    CxTime.from_seconds(time_span.total_seconds()).pretty_string
                )
            )

    def __exit__(self, exc_type, exc_val, exc_tb):
        result = False
        if exc_type is None:
            pass
        elif issubclass(exc_type, SafeError):
            appenv.say("[red]错误：{}[/]".format(exc_val))
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
        prev_key = None
        for a in self.arguments:
            if a.startswith("-"):
                prev_key = a
                continue
            if "." in a and prev_key != "-i":
                yield a

    async def _random_task_description(self):
        input_files = [Path(x).name for x in self.input_files()]
        output_files = [Path(x).name for x in self.output_files()]
        for name in itertools.cycle(input_files + output_files):
            try:
                self._task_description = name
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break

    async def execute(self, args: Iterable[str]):
        task_id = appenv.progress.add_task("[green]正在开始...[/]", total=None)

        m, n = len(list(self.input_files())), len(list(self.output_files()))
        sumary = f"[blue][{m}->{n}][/]"

        @self.ffmpeg.on("status_updated")
        def on_status_updated(status: FFmpegCodingInfo):
            current = status.current_time.total_seconds
            total = status.total_time.total_seconds if status.total_time else None

            speed = "[bright_black][{:.2f}x][/]".format(status.current_speed)
            desc = f"{sumary}{speed}[green]{self._task_description}[/]"
            appenv.progress.update(
                task_id,
                completed=current,
                total=total,
                description=desc,
            )

        ff_task = asyncio.create_task(self.ffmpeg.execute(args))
        desc_task = asyncio.create_task(self._random_task_description())

        while not ff_task.done():
            await asyncio.sleep(0.01)
            if appenv.wanna_quit_event.is_set():
                self.ffmpeg.cancel()
                break

        await asyncio.wait([ff_task])
        desc_task.cancel()
        return ff_task.result()

    def run(self) -> bool:
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

        if not inputs:
            raise SafeError("No input files provided.")

        if not outputs:
            raise SafeError("No output files provided.")

        for i in inputs:
            if not Path(i).exists():
                raise SafeError(f"输入文件 {i} 不存在。")

        existed_outputs = [x for x in outputs if Path(x).exists()]
        if existed_outputs and "-y" not in self.arguments:
            appenv.whisper(IndexedListPanel(existed_outputs, title="已存在的输出文件"))
            raise SafeError("请使用 -y 参数覆盖已存在的文件。")

        non_exist_dirs = filter(
            lambda x: not x.exists(), [Path(a).parent for a in outputs]
        )
        if non_exist_dirs:
            for d in non_exist_dirs:
                d.mkdir(parents=True, exist_ok=True)
            appenv.whisper(IndexedListPanel(non_exist_dirs, title="创建的输出目录"))

        result = asyncio.run(self.execute(self.arguments))

        appenv.whisper("运行结果：{}".format(result))

        if not result:
            if self.ffmpeg.is_canceled:
                raise SafeError("[blue]用户取消了操作。[/]")
            else:
                raise SafeError("[red]操作失败，请排查问题。[/]")

        return result
