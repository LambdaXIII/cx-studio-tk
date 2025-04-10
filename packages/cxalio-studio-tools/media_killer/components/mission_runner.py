import itertools
from cx_studio.core.cx_time import CxTime
from cx_studio.ffmpeg import (
    FFmpegAsync,
    FFmpegProcessInfo,
    FFmpegCodingInfo,
    FFmpegError,
)
from media_killer.appenv import appenv
from .mission import Mission
from .preset import Preset
import asyncio
from cx_tools_common.rich_gadgets import ProgressTaskAgent

from collections.abc import Iterable


class IOConflictError(FFmpegError):
    def __init__(self, message: str, output: str | None = None) -> None:
        super().__init__(message, output)


class MissionFailedError(FFmpegError):
    def __init__(self, message: str, output: str | None = None) -> None:
        super().__init__(message, output)


class MissionRunner:
    def __init__(self, mission: Mission):
        self._mission = mission
        self._task_agent = ProgressTaskAgent(
            task_name=f"{self._mission.name}", progress=appenv.progress
        )

        self._output_files = set(self._mission.iter_output_filenames())
        self._input_files = set(self._mission.iter_input_filenames())
        self._input_files.add(self._mission.source)

        self._well_done = None

    async def __aenter__(self):
        self._task_agent.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._task_agent.stop()
        result = False

        if exc_type is None:
            pass
        elif exc_type is KeyboardInterrupt:
            pass
        elif exc_type is FFmpegError:
            appenv.say(f"{exc_val}")
            result = True

        if not self._well_done:
            await self.__clear_output_files()

        return result

    async def __clear_output_files(self):
        safe_output_files = self._output_files - self._input_files
        for file in safe_output_files:
            if file.exists():
                file.unlink()
                appenv.whisper(f"删除目标文件 {file}")

    async def run(self):
        self._task_agent.show()

        conflicted_files = self._input_files & self._output_files
        if conflicted_files:
            raise IOConflictError(
                f"输入输出文件冲突：{conflicted_files} （这些文件已存在）"
            )

        output_dirs = {x.parent for x in self._output_files}
        for output_dir in itertools.filterfalse(lambda x: x.exists(), output_dirs):
            appenv.whisper(f"创建目标目录 {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)

        ffmpeg = FFmpegAsync(self._mission.preset.ffmpeg)

        @ffmpeg.on("started")
        def on_started(_coding_info, _process_info: FFmpegProcessInfo):
            appenv.whisper(
                "{} -> {} 转码开始…".format(
                    _process_info.start_time, self._mission.name
                )
            )

        @ffmpeg.on("progress_updated")
        def on_progress_updated(
            _coding_info: FFmpegCodingInfo, _process_info: FFmpegProcessInfo
        ):
            total_duration = _process_info.media_duration
            total: float | None = (
                total_duration.total_seconds if total_duration else None
            )
            current: float = _coding_info.current_time.total_seconds
            self._task_agent.set_progress(current, total)

        @ffmpeg.on("finished")
        def on_finished(_coding_info, _process_info: FFmpegProcessInfo):
            time_span = _process_info.time_took
            cx_time = CxTime.from_seconds(time_span.total_seconds())
            appenv.whisper(
                "{} -> {} 转码完成，耗时 {}".format(
                    _process_info.end_time, self._mission.name, cx_time.pretty_string
                )
            )

        ffmpeg_task = asyncio.create_task(ffmpeg.run(self._mission.iter_arguments()))

        while not ffmpeg_task.done():
            await asyncio.sleep(0.1)
            if appenv.wanna_quit:
                ffmpeg.cancel()
                break

        result = (await asyncio.gather(ffmpeg_task))[0]
        if not result:
            self._well_done = False
            raise MissionFailedError("{} 转码失败".format(self._mission.name))
        else:
            self._well_done = True
