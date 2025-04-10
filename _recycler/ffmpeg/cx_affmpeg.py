import asyncio
import dataclasses
import re
from collections import defaultdict
from collections.abc import Iterable, Callable
from datetime import datetime
from pathlib import Path

from cx_studio.core import CxTime
from cx_studio.path_expander import CmdFinder
from .cx_ffmpeg_common import FFmpegEventLiteral, FFmpegEventHandler
from .cx_ffmpeg_exceptions import NoFFmpegExecutableError
from .cx_ffmpeg_infos import FFmpegCodingInfo, FFmpegProcessInfo
from types import CoroutineType
from functools import wraps


class FFmpegAsync:
    def __init__(self, ffmpeg_executable: str | None = None) -> None:
        self._executable = CmdFinder.which(ffmpeg_executable or "ffmpeg")
        self._event_handlers: dict[
            FFmpegEventLiteral,
            list[
                Callable[[FFmpegCodingInfo | None, FFmpegProcessInfo], None]
                | CoroutineType
            ],
        ] = defaultdict(list)
        self._wanna_cancel = asyncio.Event()
        self._is_not_running = asyncio.Condition()

    @property
    def executable(self) -> Path | None:
        return self._executable

    def cancel(self):
        self._wanna_cancel.set()

    def is_running(self) -> bool:
        return not self._is_not_running.locked()

    def on(self, event: FFmpegEventLiteral):
        """安装事件监听器
        事件监听器的签名为： Callable[[FFmpegCodingInfo|None,FFmpegProcessInfo],None]
        """

        def decorator(handler):
            @wraps(handler)
            async def wrapper(*args, **kwargs):
                handler(*args, **kwargs)

            self._event_handlers[event].append(wrapper)
            return handler

        return decorator

    def install_event_handler(
        self, event: FFmpegEventLiteral, handler: FFmpegEventHandler
    ):
        self._event_handlers[event].append(handler)
        return self

    async def __emit(
        self,
        event: FFmpegEventLiteral,
        coding_info: FFmpegCodingInfo | None,
        process_info: FFmpegProcessInfo,
    ):
        handlers = []
        for handler in self._event_handlers[event]:
            handlers.append(asyncio.create_task(handler(coding_info, process_info)))
        await asyncio.gather(*handlers)

    async def run(self, arguments: str | list | Iterable) -> bool:
        if not self._executable:
            raise NoFFmpegExecutableError("No ffmpeg executable found")

        self._wanna_cancel.clear()

        args = [
            str(x)
            for x in (arguments.split(" ") if isinstance(arguments, str) else arguments)
        ]

        process = await asyncio.create_subprocess_exec(
            self._executable,
            *args,
            stdin=asyncio.subprocess.PIPE,
            # stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            basic_process_info = FFmpegProcessInfo(
                bin=str(self._executable), args=args, start_time=datetime.now()
            )

            await self.__emit("started", None, basic_process_info)

            async def scan_lines(stream: asyncio.StreamReader):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    cancel_loop = False

                    line = line.decode("utf-8")
                    coding_info = FFmpegCodingInfo.parse_status_line(line)

                    await self.__emit("verbose", coding_info, basic_process_info)

                    if basic_process_info.media_duration is None:
                        match = re.search(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", line)
                        if match:
                            duration = CxTime.from_timestamp(match.group(1))
                            basic_process_info = dataclasses.replace(
                                basic_process_info, media_duration=duration
                            )

                    line = line.strip()
                    if line.startswith("frame="):
                        coding_info = FFmpegCodingInfo.parse_status_line(line)
                        await self.__emit(
                            "progress_updated", coding_info, basic_process_info
                        )

                    if self._wanna_cancel.is_set():
                        await asyncio.wait_for(
                            process.communicate("q".encode("utf-8")), 5
                        )
                        if process.returncode is None:
                            process.kill()
                        await self.__emit("canceled", coding_info, basic_process_info)
                        cancel_loop = True

                    await asyncio.sleep(delay=0.1)

                    if cancel_loop:
                        break
                # async for

            # scan_lines
        except asyncio.CancelledError:
            await self.__emit("canceled", None, basic_process_info)

        finally:
            await process.wait()
            basic_process_info = dataclasses.replace(
                basic_process_info, end_time=datetime.now()
            )
            await self.__emit("finished", None, basic_process_info)
            return process.returncode == 0
