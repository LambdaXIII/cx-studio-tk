import asyncio
from .cx_ff_infos import FFmpegCodingInfo
from .utils.basic_ffmpeg import BasicFFmpeg
from pyee.asyncio import AsyncIOEventEmitter
from collections.abc import Iterable
from pathlib import Path
from cx_studio.path_expander import CmdFinder
from cx_studio.utils import AsyncStreamUtils
import signal, sys
import re
from cx_studio.core import CxTime, FileSize
from copy import copy


class FFmpegAsync(AsyncIOEventEmitter):
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

    @property
    def executable(self) -> str:
        return self._executable

    @property
    def coding_info(self) -> FFmpegCodingInfo:
        return copy(self._coding_info)

    async def _handle_stderr(self):
        stream = AsyncStreamUtils.wrap_io(self._process.stderr)
        async for line in AsyncStreamUtils.readlines_from_stream(stream):
            line_str = line.decode("utf-8", errors="ignore")
            self.emit("verbose", line_str)

            coding_info_dict = FFmpegCodingInfo.parse_status_line(line_str)

            self._coding_info.update(**coding_info_dict)

            if "current_time" in coding_info_dict or "total_time" in coding_info_dict:
                self.emit(
                    "progress_updated",
                    self._coding_info.current_time,
                    self._coding_info.total_time,
                )

            if "current_frame" in coding_info_dict:
                self.emit("status_updated", copy(self._coding_info))
        # for

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

    async def _redirect_input(self, input_stream: asyncio.StreamReader | bytes | None):
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
        async with self._is_running:
            self._process = await AsyncStreamUtils.create_subprocess(
                self._executable,
                *args,
                stdin=asyncio.subprocess.PIPE if input_stream else None,
                # stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self.emit("started")

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
                # self._canceled = True
                self.cancel()

            finally:
                await self._process.wait()
                result = self._process.returncode == 0
                if self._canceled:
                    self.emit("canceled")
                elif result is False:
                    self.emit("terminated")
                else:
                    self.emit("finished")
                return result
        # running condition

    async def _parse_basic_info_from_stream(
        self, input_stream: asyncio.StreamReader
    ) -> dict:
        result = {}
        streams = []
        async for line in AsyncStreamUtils.readlines_from_stream(input_stream):
            line_str = line.decode()
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
        if len(streams) > 0:
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
