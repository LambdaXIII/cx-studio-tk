import asyncio
from .cx_ff_infos import FFmpegCodingInfo
from .utils.basic_ffmpeg import BasicFFmpeg
from pyee.asyncio import AsyncIOEventEmitter
from collections.abc import Iterable
from pathlib import Path
from cx_studio.path_expander import CmdFinder
from cx_studio.utils import AsyncStreamUtils
import signal,sys
import re
from cx_studio.core import CxTime, FileSize

class FFmpegAsync(AsyncIOEventEmitter, BasicFFmpeg):
    def __init__(
        self,
        ffmpeg_executable: str | Path | None = None,
        arguments: Iterable[str] | None = None,
    ):
        super().__init__()
        self._executable: str = str(CmdFinder.which(ffmpeg_executable or "ffmpeg"))
        self._arguments = list(arguments or [])
        self._coding_info = FFmpegCodingInfo()

        self._is_running = asyncio.Condition()
        self._cancel_event = asyncio.Event()
        self._process:asyncio.subprocess.Process

    async def _handle_stderr(self):
        stream = AsyncStreamUtils.wrap_io(self._process.stderr)
        async for line in AsyncStreamUtils.readlines_from_stream(stream):
            line_str = line.decode("utf-8", errors="ignore")
            self.emit("verbose",line_str)

            coding_info = FFmpegCodingInfo.from_status_line(line_str)
            self._coding_info.update_from(coding_info)

            if coding_info.current_time or coding_info.total_time:
                self.emit("progress_updated",self._coding_info.current_time,self._coding_info.total_time)

            if coding_info.current_frame:
                self.emit("status_updated",self._coding_info)
        # for

    def is_running(self) -> bool:
        return self._is_running.locked()

    def cancel(self):
        self._cancel_event.set()
        # await asyncio.wait_for(self._process.communicate(b"q"),5)
        

    async def _hold_cancel(self):
        await self._cancel_event.wait()
        sigterm = signal.SIGTERM if sys.platform != "win32" else signal.CTRL_BREAK_EVENT
        self._process.send_signal(sigterm)
        if not self._process.returncode:
            self._process.terminate()
            await self._process.wait()
        self._cancel_event.clear()

    async def execute(self) -> bool:
        self._cancel_event.clear()
        async with self._is_running:
            self._process = await AsyncStreamUtils.create_subprocess(
                self._executable,
                *self.iter_arguments(),
                stdin=asyncio.subprocess.PIPE,
                # stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self.emit("started")
            canceled = False

            try:
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self._handle_stderr())
                    tg.create_task(self._hold_cancel())
            except asyncio.CancelledError:
                # self.cancel()
                pass
            finally:
                await self._process.wait()
                result = self._process.returncode==0 and not canceled
                if canceled:
                    self.emit("canceled")
                else:
                    self.emit("finished",result)
                return result
        #running condition
            
    async def _parse_basic_info_from_stream(self,input_stream:asyncio.StreamReader) -> dict:
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
                result["start_time"] = CxTime.from_seconds(
                    float(time_match.group(2))
                )
                result["bitrate"] = FileSize.from_string(time_match.group(3))
                continue

            streams_match = re.search(r"Stream #0:\d+\s+", line_str)
            if streams_match:
                streams.append(line_str.strip())
                continue
        if len(streams) > 0:
            result["streams"] = streams
        return result


    async def get_basic_info(self,filename:Path) -> dict:
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
