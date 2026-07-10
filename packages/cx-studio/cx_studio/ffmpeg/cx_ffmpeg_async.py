import asyncio
import re
import signal
import sys
from collections.abc import Iterable
from copy import copy
from pathlib import Path

from pyee.asyncio import AsyncIOEventEmitter

from cx_studio.core import CxTime, FileSize
from cx_studio.filesystem.path_expander import CmdFinder
from cx_studio.iotools import AsyncStreamUtils
from typing import Any
from .cx_ff_infos import FFmpegCodingInfo

# ── FFmpegAsync 事件名常量 ────────────────────────────────────
# 消费者应引用这些常量而非裸字符串，避免拼写错误。

# FFmpeg 子进程已启动：()
# 在 create_subprocess 成功后、stderr 读取开始前发射。
FFMPEG_EVENT_STARTED: str = "started"

# 转码进度更新：(current: CxTime, total: CxTime | None)
# 每解析到含 current_time 或 total_time 的 stderr 行时发射。
FFMPEG_EVENT_PROGRESS_UPDATED: str = "progress_updated"

# 帧级状态更新：(coding_info: FFmpegCodingInfo)
# 每解析到含 current_frame 的 stderr 行时发射。
FFMPEG_EVENT_STATUS_UPDATED: str = "status_updated"

# FFmpeg 进程正常退出（returncode == 0）：()
# 在 process.wait() 完成后发射。
FFMPEG_EVENT_FINISHED: str = "finished"

# FFmpeg 进程被取消（用户中断）：()
# 在 cancel_event 触发导致进程终止后发射。
FFMPEG_EVENT_CANCELED: str = "canceled"

# FFmpeg 进程异常退出（returncode != 0，非取消）：
#   (exit_code: int, stderr_lines: list[str])
# 在 process.wait() 完成后发射。stderr_lines 是完整的 stderr 行缓存，
# 消费者可从中提取错误诊断信息。
FFMPEG_EVENT_TERMINATED: str = "terminated"

# FFmpeg 原始 stderr 行：(line: str)
# 每读取到一行 stderr 时发射。高频事件，消费者应谨慎处理。
FFMPEG_EVENT_VERBOSE_UPDATED: str = "verbose_updated"


class FFmpegAsync(AsyncIOEventEmitter):
    """异步 FFmpeg 子进程封装。

    通过 asyncio 管理 FFmpeg 子进程，通过事件报告进度与状态。
    使用 ``AsyncIOEventEmitter``，所有事件 handler 在事件发射时同步调用。

    事件（消费者应引用 ``FFMPEG_EVENT_*`` 常量而非裸字符串）：

    | 事件常量 | 事件名 | 参数 | 说明 |
    |---|---|---|---|
    | ``FFMPEG_EVENT_STARTED`` | ``started`` | ``()`` | 子进程已启动 |
    | ``FFMPEG_EVENT_PROGRESS_UPDATED`` | ``progress_updated`` | ``(current: CxTime, total: CxTime | None)`` | 转码进度 |
    | ``FFMPEG_EVENT_STATUS_UPDATED`` | ``status_updated`` | ``(coding_info: FFmpegCodingInfo)`` | 帧级状态 |
    | ``FFMPEG_EVENT_FINISHED`` | ``finished`` | ``()`` | 进程正常退出 |
    | ``FFMPEG_EVENT_CANCELED`` | ``canceled`` | ``()`` | 进程被取消 |
    | ``FFMPEG_EVENT_TERMINATED`` | ``terminated`` | ``(exit_code: int, stderr_lines: list[str])`` | 进程异常退出，携带退出码和完整 stderr 行 |
    | ``FFMPEG_EVENT_VERBOSE_UPDATED`` | ``verbose_updated`` | ``(line: str)`` | 原始 stderr 行，高频 |
    """

    def __init__(
        self,
        ffmpeg_executable: str | Path | None = None,
    ):
        super().__init__()
        self._executable: str = str(CmdFinder.which(ffmpeg_executable or "ffmpeg"))
        self._coding_info = FFmpegCodingInfo()

        self._is_running = asyncio.Condition()
        self._cancel_event = asyncio.Event()
        self._canceled = False
        self._process: asyncio.subprocess.Process
        # stderr 行缓存——每次 execute() 开始时清空，
        # 在 terminated 事件中传给消费者供错误诊断
        self._stderr_lines: list[str] = []

    @property
    def is_canceled(self) -> bool:
        return self._canceled

    @property
    def executable(self) -> str:
        return self._executable

    @property
    def coding_info(self) -> FFmpegCodingInfo:
        return copy(self._coding_info)

    @property
    def return_code(self) -> int | None:
        """最后一次 execute() 的进程退出码。

        进程未启动或仍在运行时为 None。execute() 返回后为 int
        （0 表示成功，非 0 表示异常退出）。
        """
        proc = getattr(self, "_process", None)
        return proc.returncode if proc is not None else None

    async def _handle_stderr(self):
        stream = AsyncStreamUtils.wrap_io(self._process.stderr)
        async for line in AsyncStreamUtils.readlines_from_stream(stream):
            line_str = line.decode("utf-8", errors="ignore")
            self.emit(FFMPEG_EVENT_VERBOSE_UPDATED, line_str)
            self._stderr_lines.append(line_str)

            coding_info_dict = FFmpegCodingInfo.parse_status_line(line_str)

            self._coding_info.update(**coding_info_dict)

            if "current_time" in coding_info_dict or "total_time" in coding_info_dict:
                self.emit(
                    FFMPEG_EVENT_PROGRESS_UPDATED,
                    self._coding_info.current_time,
                    self._coding_info.total_time,
                )

            if "current_frame" in coding_info_dict:
                self.emit(FFMPEG_EVENT_STATUS_UPDATED, copy(self._coding_info))

    def is_running(self) -> bool:
        return self._is_running.locked()

    def cancel(self):
        self._cancel_event.set()

    async def terminate(self):
        sigterm = signal.SIGTERM if sys.platform != "win32" else signal.CTRL_BREAK_EVENT
        self._process.send_signal(sigterm)
        try:
            await asyncio.wait_for(self._process.wait(), 4)
        except asyncio.TimeoutError:
            self._process.terminate()

    async def _redirect_input(
        self, input_stream: asyncio.StreamReader | bytes | None
    ) -> None:
        input_stream = AsyncStreamUtils.wrap_io(input_stream)
        if self._process.stdin is None:
            return
        await AsyncStreamUtils.redirect_stream(input_stream, self._process.stdin)
        self._process.stdin.close()

    async def execute(
        self,
        arguments: Iterable[str] | None = None,
        input_stream: asyncio.StreamReader | bytes | None = None,
    ) -> bool:
        args = list(arguments or [])
        self._cancel_event.clear()
        self._canceled = False
        self._stderr_lines.clear()
        async with self._is_running:
            self._process = await AsyncStreamUtils.create_subprocess(
                self._executable,
                *args,
                stdin=asyncio.subprocess.PIPE if input_stream else None,
                stderr=asyncio.subprocess.PIPE,
            )

            self.emit(FFMPEG_EVENT_STARTED)

            i_stream = AsyncStreamUtils.wrap_io(input_stream)

            try:
                main_task = asyncio.create_task(self._handle_stderr())
                tasks = [main_task]
                if input_stream and self._process.stdin:
                    redirect_task = asyncio.create_task(
                        AsyncStreamUtils.redirect_stream(i_stream, self._process.stdin)
                    )
                    tasks.append(redirect_task)

                while not main_task.done():
                    if self._cancel_event.is_set():
                        self._canceled = True
                        sigterm = (
                            signal.SIGTERM
                            if sys.platform != "win32"
                            else signal.CTRL_BREAK_EVENT
                        )
                        self._process.send_signal(sigterm)
                        try:
                            await asyncio.wait_for(self._process.wait(), 4)
                        except asyncio.TimeoutError:
                            self._process.terminate()
                        self._cancel_event.clear()
                    await asyncio.sleep(0.1)
                await asyncio.wait(tasks)

            except asyncio.CancelledError:
                self.cancel()

            finally:
                await self._process.wait()
                result = self._process.returncode == 0
                if self._canceled:
                    self.emit(FFMPEG_EVENT_CANCELED)
                elif result is False:
                    self.emit(
                        FFMPEG_EVENT_TERMINATED,
                        self._process.returncode,
                        self._stderr_lines,
                    )
                else:
                    self.emit(FFMPEG_EVENT_FINISHED)
            return result
        # running condition

    async def _parse_basic_info_from_stream(
        self, input_stream: asyncio.StreamReader
    ) -> dict[str, Any]:
        result = {}
        streams = []
        async for line in AsyncStreamUtils.readlines_from_stream(input_stream):
            line_str = line.decode("utf-8", errors="ignore")
            input_match = re.match(r"Input #0, (.+), from '(.+)':", line_str)
            if input_match:
                result["format_name"] = input_match.group(1)
                result["file_name"] = input_match.group(2)
                continue

            time_match = re.search(
                r"Duration: (.+), start: (.+), bitrate: (\d+\.?\d*\s?\w+)/s",
                line_str,
            )
            if time_match:
                result["duration"] = CxTime.from_timestamp(time_match.group(1))
                result["start_time"] = CxTime.from_seconds(float(time_match.group(2)))
                result["bitrate"] = FileSize.from_string(time_match.group(3))
                continue

            streams_match = re.search(r"Stream #0:\d+\s+", line_str)
            if streams_match:
                streams.append(line_str.strip())
                continue
        if streams:
            result["streams"] = streams
        return result

    async def get_basic_info(self, filename: Path) -> dict:
        async with self._is_running:
            self._process = await AsyncStreamUtils.create_subprocess(
                self._executable,
                "-i",
                str(filename),
                stderr=asyncio.subprocess.PIPE,
            )

            stream = AsyncStreamUtils.wrap_io(self._process.stderr)
            result = await self._parse_basic_info_from_stream(stream)
            await self._process.wait()
            return result
