import itertools
import os
from turtle import title
from cx_studio.core.cx_time import CxTime
from cx_studio.ffmpeg import FFmpegAsync
from cx_studio.utils import PathUtils
from cx_studio.ffmpeg import FFmpegCodingInfo
from cx_tools_common.rich_gadgets.indexed_list_panel import IndexedListPanel
from media_killer.appenv import appenv
from .mission import Mission
from .preset import Preset
import asyncio
from cx_tools_common.rich_gadgets import ProgressTaskAgent

from collections.abc import Iterable
from cx_tools_common.rich_gadgets import RichLabel
from rich.text import Text
from rich.columns import Columns
import itertools
from datetime import datetime
from pathlib import Path


class MissionRunner:
    def __init__(self, mission: Mission):
        self.mission = mission
        self._ffmpeg: FFmpegAsync = FFmpegAsync(self.mission.preset.ffmpeg)
        self._input_files = [self.mission.source] + list(
            self.mission.iter_input_filenames()
        )
        self._output_files = [self.mission.standard_target] + list(
            self.mission.iter_output_filenames()
        )

        self._task_description: str = self.mission.name
        self._task_completed: float = 0
        self._task_total: float | None = None

        self._cancel_event = asyncio.Event()
        # self._canceled = False
        # self._cancelling_cond = asyncio.Condition()
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._running_cond = asyncio.Condition()
        self._ffmpeg_outputs = []

    def cancel(self):
        self._canceled = True
        self._cancel_event.set()

    @property
    def task_description(self):
        return self._task_description

    @property
    def task_completed(self):
        return self._task_completed

    @property
    def task_total(self):
        return self._task_total

    @property
    def task_start_time(self):
        return self._start_time

    @property
    def task_end_time(self):
        return self._end_time

    def done(self):
        return self._start_time is not None and self._end_time is not None

    def is_running(self):
        return self._running_cond.locked()

    def make_line_report(self, right_side: str):
        misison_label = RichLabel(self.mission)
        r = Text.from_markup(right_side, justify="right", overflow="ignore")
        return Columns([misison_label, r], expand=True)

    async def _on_started(self, *args):
        appenv.whisper(self.make_line_report("[yellow]开始[/]"))

    async def _on_progress_updated(self, c: CxTime, t: CxTime | None):
        c_seconds = c.total_seconds
        t_seconds = t.total_seconds if t else None
        self._task_completed = c_seconds
        self._task_total = t_seconds

    async def _on_finished(self):
        appenv.say(self.make_line_report("[green]完成[/]"))

    async def _on_terminated(self):
        appenv.say(self.make_line_report("[red]运行异常[/]"))
        await self._clean_up()

    async def _on_canceled(self):
        appenv.say(self.make_line_report("[bright_blue]被取消[/]"))
        await self._clean_up()
        self._cancel_event.clear()

    async def _clean_up(self):
        appenv.whisper(IndexedListPanel(self._ffmpeg_outputs),title="FFmpeg 输出")
        self._ffmpeg_outputs.clear()
        safe_outputs = set(self._output_files) - set(self._input_files)
        deleting_files = set(filter(lambda x: x.exists(), safe_outputs))
        if deleting_files:
            appenv.whisper(IndexedListPanel(deleting_files, title="未完成的目标文件"))
            appenv.add_garbage_files(*deleting_files)

    async def _on_verbose(self,line:str):
        self._ffmpeg_outputs.append(line)

        

    async def _holding_cancel(self):
        await self._cancel_event.wait()
        self._ffmpeg.cancel()

    async def execute(self):
        async with self._running_cond:
            self._start_time = datetime.now()

            conflits = set(self._input_files) & set(self._output_files)
            if len(conflits) > 0:
                appenv.say(self.make_line_report(f"[red]检测到重叠的输入输出文件[/]"))
                appenv.whisper(IndexedListPanel(conflits, title="重叠文件"))
                await self._on_canceled()
                return

            if not PathUtils.is_executable(Path(self._ffmpeg.executable)):
                appenv.say(self.make_line_report(f"[red]ffmpeg可执行文件无效[/]"))
                appenv.whisper(self._ffmpeg.executable)
                await self._on_canceled()
                return

            o_dirs = set(map(lambda x: x.parent, self._output_files))
            invalid_o_dirs = set(
                itertools.filterfalse(
                    lambda x: os.access(x, os.W_OK),
                    filter(lambda x: x.exists(), o_dirs),
                )
            )
            if invalid_o_dirs:
                appenv.say(self.make_line_report(f"[red]输出目录无效[/]"))
                appenv.whisper(IndexedListPanel(invalid_o_dirs, title="无效输出目录"))
                await self._on_canceled()
                return

            non_existent_o_dirs = set(
                itertools.filterfalse(lambda x: x.exists(), o_dirs)
            )
            if non_existent_o_dirs:
                self._task_description = "创建目标文件夹"
                for x in non_existent_o_dirs:
                    x.mkdir(parents=True, exist_ok=True)
                appenv.whisper(
                    IndexedListPanel(non_existent_o_dirs, title="创建的目标文件夹")
                )

            self._ffmpeg.add_listener("started", self._on_started)
            self._ffmpeg.add_listener("progress_updated", self._on_progress_updated)
            self._ffmpeg.add_listener("finished", self._on_finished)
            self._ffmpeg.add_listener("canceled", self._on_canceled)
            self._ffmpeg.add_listener("terminated", self._on_terminated)
            self._ffmpeg.add_listener("verbose",self._on_verbose)

            ffmpeg_outputs = []

            try:
                async with asyncio.TaskGroup() as task_group:
                    cancel_task = task_group.create_task(self._holding_cancel())
                    main_task = task_group.create_task(
                        self._ffmpeg.execute(self.mission.iter_arguments())
                    )
                    await main_task
                    if not cancel_task.done():
                        cancel_task.cancel()
                        await cancel_task
            finally:
                # async with self._cancelling_cond:
                self._end_time = datetime.now()
                await self._ffmpeg.wait_for_complete()
                result = main_task.result()
                # if not result:
                #     appenv.whisper(
                #         IndexedListPanel(
                #             ffmpeg_outputs, title="FFMPEG 输出", max_lines=1000
                #         )
                #     )
                return result

        # running condition
