import asyncio
import dataclasses
import re
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from cx_studio.core import CxTime
from cx_studio.path_expander import CmdFinder
from .cx_ffmpeg_common import FFmpegEventLiteral, FFmpegEventHandler
from .cx_ffmpeg_exceptions import NoFFmpegExecutableError
from .cx_ffmpeg_infos import FFmpegCodingInfo, FFmpegProcessInfo


class FFmpegAsync:
    def __init__(self, ffmpeg_executable: str | None = None) -> None:
        self._executable = CmdFinder.which(ffmpeg_executable or "ffmpeg")
        self._event_handlers: dict[FFmpegEventLiteral, list[FFmpegEventHandler]] = (
            defaultdict(list)
        )
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
            self._event_handlers[event].append(handler)
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
            *args,
            **kwargs,
    ):
        for handler in self._event_handlers[event]:
            handler(coding_info, process_info, *args, **kwargs)

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

        basic_process_info = FFmpegProcessInfo(
            bin=str(self._executable), args=args, start_time=datetime.now()
        )

        await self.__emit("started", None, basic_process_info)

        async for line in process.stderr:
            emitters = []

            line = line.decode("utf-8")
            coding_info = FFmpegCodingInfo.parse_status_line(line)

            emitters.append(
                asyncio.create_task(
                    self.__emit("verbose", coding_info, basic_process_info)
                )
            )

            if basic_process_info.media_duration is None:
                match = re.search(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", line)
                if match:
                    duration = CxTime.from_timestamp(match.group(1))
                    basic_process_info = dataclasses.replace(
                        basic_process_info, media_duration=duration
                    )

            if line.startswith("frame="):
                coding_info = FFmpegCodingInfo.parse_status_line(line)
                emitters.append(
                    asyncio.create_task(
                        self.__emit("progress_updated", coding_info, basic_process_info)
                    )
                )

            if self._wanna_cancel.is_set():
                await asyncio.wait_for(process.communicate("q".encode("utf-8")), 3)
                if process.returncode is not None:
                    process.terminate()
                await self.__emit("canceled", coding_info, basic_process_info)
                break

            await asyncio.gather(*emitters)
            await asyncio.sleep(0.1)

        await process.wait()
        basic_process_info = dataclasses.replace(
            basic_process_info, end_time=datetime.now()
        )
        await self.__emit("finished", None, basic_process_info)
        return process.returncode == 0
