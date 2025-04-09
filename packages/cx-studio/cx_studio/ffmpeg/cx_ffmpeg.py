from collections.abc import Iterable
from datetime import datetime
import subprocess
import asyncio
from collections import defaultdict
from functools import wraps
from pathlib import Path
import re, dataclasses
from typing import Literal

from cx_studio.core import FileSize, CxTime
from cx_studio.path_expander import CmdFinder
from .cx_ffmpeg_exceptions import NoFFmpegExecutableError
from .cx_ffmpeg_infos import FFmpegCodingInfo, FFmpegProcessInfo

FFmpegEventLiteral = Literal[
    "started", "finished", "cancelled", "progress_updated", "verbose"
]


class FFmpeg:
    def __init__(self, ffmpeg_executable: str | None = None) -> None:
        self._executable = CmdFinder.which(ffmpeg_executable or "ffmpeg")
        self._event_handlers = defaultdict(list)
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
        def decorator(func):
            self._event_handlers[event].append(func)
            return func

        return decorator

    def get_basic_info(self, source: str | Path) -> dict:
        if not self._executable:
            raise NoFFmpegExecutableError("No ffmpeg executable found.")

        result = {}
        streams = []

        args = [self._executable, "-hide_banner", "-i", source]

        with subprocess.Popen(
            args,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            errors="ignore",
            universal_newlines=True,
            encoding="utf-8",
        ) as process:
            for line in process.stderr or []:
                input_match = re.match(r"Input #0, (.+), from '(.+)':", line)
                if input_match:
                    result["format_name"] = input_match.group(1)
                    result["file_name"] = input_match.group(2)
                    continue

                time_match = re.search(
                    r"Duration: (.+), start: (.+), bitrate: (\d+\.?\d*\s?\w+)/s",
                    line,
                )
                if time_match:
                    result["duration"] = CxTime.from_timestamp(time_match.group(1))
                    result["start_time"] = CxTime.from_seconds(
                        float(time_match.group(2))
                    )
                    result["bitrate"] = FileSize.from_string(time_match.group(3))
                    continue

                streams_match = re.search(r"Stream #0:\d+\s+", line)
                if streams_match:
                    streams.append(line.strip())
                    continue

            process.wait()
        # process

        if len(streams) > 0:
            result["streams"] = streams
        return result

    def __emit(self, event: FFmpegEventLiteral, *args, **kwargs):
        if event not in self._event_handlers:
            return
        for handler in self._event_handlers[event]:
            handler(*args, **kwargs)

    async def __aemit(self, event: FFmpegEventLiteral, *args, **kwargs):
        if event not in self._event_handlers:
            return
        for handler in self._event_handlers[event]:
            handler(*args, **kwargs)

    def run(self, arguments: str | list | Iterable) -> bool:
        if not self._executable:
            raise NoFFmpegExecutableError("No ffmpeg executable found.")

        args = [
            str(x)
            for x in (arguments.split(" ") if isinstance(arguments, str) else arguments)
        ]
        args.insert(0, str(self._executable))

        with subprocess.Popen(
            args,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="ignore",
            universal_newlines=True,
        ) as process:

            basic_process_info = FFmpegProcessInfo(
                bin=str(self._executable), args=args, start_time=datetime.now()
            )
            self.__emit("started", basic_process_info)

            for line in process.stderr or []:
                if basic_process_info.media_duration is None:
                    match = re.match(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", line)
                    if match:
                        duration = CxTime.from_timestamp(match.group(1))
                        basic_process_info = dataclasses.replace(
                            basic_process_info, media_duration=duration
                        )

                line = line.strip()
                self.__emit("verbose", line)

                if line.startswith("frame="):
                    coding_status = FFmpegCodingInfo.parse_status_line(line)
                    self.__emit("progress_updated", basic_process_info, coding_status)

                if self._wanna_cancel.is_set():
                    process.communicate("q")
                    process.wait(3)
                    if process.returncode == 0:
                        process.kill()
                        self.__emit("cancelled", basic_process_info)
                    break
            # for
            process.wait()
        # process

        basic_process_info = dataclasses.replace(
            basic_process_info, end_time=datetime.now()
        )
        self.__emit("finished", basic_process_info)
        return process.returncode == 0

    async def arun(self, arguments: str | list | Iterable) -> bool:
        if not self._executable:
            raise NoFFmpegExecutableError("No ffmpeg executable found.")

        args = [
            str(x)
            for x in (arguments.split(" ") if isinstance(arguments, str) else arguments)
        ]
        args.insert(0, str(self._executable))

        async with self._is_not_running:
            with subprocess.Popen(
                args,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="ignore",
                universal_newlines=True,
            ) as process:

                basic_process_info = FFmpegProcessInfo(
                    bin=str(self._executable), args=args, start_time=datetime.now()
                )
                await self.__aemit("started", basic_process_info)

                for line in process.stderr or []:
                    if basic_process_info.media_duration is None:
                        match = re.match(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", line)
                        if match:
                            duration = CxTime.from_timestamp(match.group(1))
                            basic_process_info = dataclasses.replace(
                                basic_process_info, media_duration=duration
                            )

                    line = line.strip()
                    if line.startswith("frame="):
                        coding_status = FFmpegCodingInfo.parse_status_line(line)
                        await self.__aemit(
                            "progress_updated", basic_process_info, coding_status
                        )

                    if self._wanna_cancel.is_set():
                        process.communicate("q")
                        process.wait(3)
                        if process.returncode == 0:
                            process.kill()
                            await self.__aemit("cancelled", basic_process_info)
                        break
                    await asyncio.sleep(0.1)
                # for
                process.wait()
            # process
        # condition

        basic_process_info = dataclasses.replace(
            basic_process_info, end_time=datetime.now()
        )
        await self.__aemit("finished", basic_process_info)
        return process.returncode == 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        result = False
        if issubclass(type(exc_value), asyncio.CancelledError):
            result = True
        return result
