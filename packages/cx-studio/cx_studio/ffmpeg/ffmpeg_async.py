"""异步 FFmpeg 子进程执行器。

基于 ``asyncio`` 管理 FFmpeg 子进程的启动、运行与结束，通过
``FFMPEG_EVENT_*`` 事件向消费者报告启动、转码进度、帧级状态以及
正常结束/取消/异常退出；并提供 ``-i`` 探测媒体基本信息的能力。
事件常量及其参数见类 ``FFmpegAsync`` 的文档。
"""

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
from cx_studio.process import AsyncStreamUtils
from typing import Any
from .ff_infos import FFmpegCodingInfo

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
        """本次 execute() 是否已被取消。

        每次 execute() 开始时重置为 False；执行期间检测到 ``cancel()``
        请求并以取消方式终止进程后为 True，直到下一次 execute()。
        """
        return self._canceled

    @property
    def executable(self) -> str:
        """当前使用的 FFmpeg 可执行文件路径。

        构造时经 ``CmdFinder.which`` 解析得到（未显式传入时默认查找
        ``"ffmpeg"``）的字符串路径。
        """
        return self._executable

    @property
    def coding_info(self) -> FFmpegCodingInfo:
        """当前转码状态的可变副本。

        返回内部 ``FFmpegCodingInfo`` 的浅拷贝（``copy.copy``），避免
        调用方直接改动实例内部状态。
        """
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
        """当前是否正在执行任务。

        基于运行锁（``asyncio.Condition``）是否被持有判断：``execute()``
        或 ``get_basic_info()`` 持锁期间返回 True，结束后返回 False。
        """
        return self._is_running.locked()

    def cancel(self):
        """请求取消当前执行的 FFmpeg 进程。

        仅设置内部取消事件；execute() 的轮询循环检测到后向进程发送
        终止信号并以取消方式结束。未在执行中调用只会残留标志，
        下一次 execute() 开头会清空它，因此不影响后续执行。
        """
        self._cancel_event.set()

    async def terminate(self):
        """终止当前运行的 FFmpeg 子进程（协程）。

        发送 SIGTERM（Windows 上为 ``CTRL_BREAK_EVENT``）并最多等待
        4 秒退出；超时则改用 ``process.terminate()`` 强制结束。
        须在进程运行期间（execute() 已启动进程后）调用，执行完毕即返回。
        """
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
        """以 ``executable + arguments`` 执行一次 FFmpeg 并等待结束（协程）。

        运行期间的行为：
        - 以管道捕获 stderr 并逐行解析：每行都发射
          ``FFMPEG_EVENT_VERBOSE_UPDATED``，解析到时间字段时发射
          ``FFMPEG_EVENT_PROGRESS_UPDATED``、解析到帧号时发射
          ``FFMPEG_EVENT_STATUS_UPDATED``（同步更新 ``coding_info``）；
        - 传入 ``input_stream`` 时将其内容经管道写入子进程 stdin
          （提供与否也决定是否分配 stdin 管道）；
        - 每 0.1 秒轮询 ``cancel()`` 请求，检测到即以终止信号取消进程，
          使 ``is_canceled`` 为 True；
        - 协程自身被取消（``CancelledError``）时同样请求取消。
        进程退出后按结果发射 ``finished``/``canceled``/``terminated`` 之一
        （参数见类 docstring 的事件表）。执行全程持有运行锁，与
        ``get_basic_info()`` 互斥；期间调用 ``is_running()`` 为 True。

        Args:
            arguments: 追加在可执行文件之后的命令行参数；
                ``None`` 或空则不追加任何参数。
            input_stream: 要写入子进程 stdin 的数据，可为字节串或
                ``asyncio.StreamReader``；``None`` 时不分配 stdin 管道。

        Returns:
            进程是否成功结束（退出码为 0）；取消/异常退出均返回 False。
        """
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
        """探测媒体文件基本信息（协程）：执行 ``ffmpeg -i <filename>`` 并解析 stderr。

        与 execute() 共用运行锁（互斥）。返回 dict 的键（解析到才出现）：
        - ``format_name``/``file_name``：来自
          ``Input #0, <格式>, from '<文件>':`` 行；
        - ``duration``/``start_time``/``bitrate``：来自
          ``Duration: hh:mm:ss.xx, start: <秒>, bitrate: <值>/s`` 行，
          时间转 ``CxTime``、码率转 ``FileSize``；
        - ``streams``：所有以 ``Stream #0:N`` 开头的行文本列表。

        Args:
            filename: 待探测的媒体文件路径。

        Returns:
            解析结果 dict；无匹配行时为 ``{}``，部分字段缺失时省略对应键。
        """
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
