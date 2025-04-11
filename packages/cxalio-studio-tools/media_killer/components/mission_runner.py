from ast import Str
import itertools
from cx_studio.core.cx_time import CxTime
from cx_studio.ffmpeg import FFmpeg
from cx_studio.ffmpeg.cx_ff_infos import FFmpegCodingInfo
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


class IOConflictError(Exception):
    def __init__(self, message: str, output: str | None = None) -> None:
        super().__init__(message, output)


class MissionRunner:
    def __init__(self, mission: Mission):
        self.mission = mission
        self._ffmpeg = FFmpeg(mission.preset.ffmpeg, mission.iter_arguments())
        self._input_files = [self.mission.source] + list(
            self.mission.iter_input_filenames()
        )
        self._output_files = [self.mission.standard_target] + list(
            self.mission.iter_output_filenames()
        )

        self._task_description: str = self.mission.name
        self._task_completed: float = 0
        self._task_total: float | None = None

    def create_target_folders(self):
        output_folders = set(map(lambda x: x.parent, self._output_files))
        for folder in output_folders:
            folder.mkdir(parents=True, exist_ok=True)

    def cancel(self):
        self._ffmpeg.cancel()

    @property
    def task_description(self):
        return self._task_description

    @property
    def task_completed(self):
        return self._task_completed

    @property
    def task_total(self):
        return self._task_total

    def run(self):
        @self._ffmpeg.on("started")
        def on_started(*args):
            appenv.whisper("Mission Started:{}".format(self.mission.name))

        @self._ffmpeg.on("progress_updated")
        def on_progress_updated(c: CxTime, t: CxTime | None):
            c_seconds = c.total_seconds
            t_seconds = t.total_seconds if t else None
            self._task_completed = c_seconds
            self._task_total = t_seconds

        @self._ffmpeg.on("finished")
        def on_finished():
            appenv.say(
                Columns(
                    [
                        RichLabel(self.mission),
                        Text("完成", style="green", justify="right"),
                    ]
                )
            )

        @self._ffmpeg.on("canceled")
        def on_canceled():
            appenv.say(
                Columns(
                    [
                        RichLabel(self.mission),
                        Text("取消", style="red", justify="right"),
                    ]
                )
            )

        self.create_target_folders()
        return self._ffmpeg.execute()
