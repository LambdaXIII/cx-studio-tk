from copy import copy
import time
from pyee import EventEmitter
from cx_studio.path_expander import CmdFinder
from pathlib import Path
from .cx_ff_infos import FFmpegCodingInfo
import threading
from collections.abc import Iterable, Generator
from cx_studio.utils import TextUtils, StreamUtils
from .utils.basic_ffmpeg import BasicFFmpeg
from typing import IO
from .cx_ff_errors import *
import io, os
import subprocess
import concurrent.futures as con_futures
import sys, signal
from cx_studio.core import CxTime, FileSize


class FFmpeg(EventEmitter):
    def __init__(self, ffmpeg_executable: str | Path | None = None):
        super().__init__()
        self._executable: str = str(CmdFinder.which(ffmpeg_executable or "ffmpeg"))
        self._coding_info = FFmpegCodingInfo()

        self._running_lock = threading.Lock()
        self._running_cond = threading.Condition(self._running_lock)
        self._cancel_event = threading.Event()
        self._canceled = False
        self._process: subprocess.Popen[bytes]

    @property
    def executable(self) -> str:
        return self._executable

    @property
    def coding_info(self) -> FFmpegCodingInfo:
        return copy(self._coding_info)

    def _handle_stderr(self, line: bytes):
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

    def is_running(self) -> bool:
        return self._running_lock.locked()

    def cancel(self):
        self._cancel_event.set()

    def terminate(self):
        sigterm = signal.SIGTERM if sys.platform != "win32" else signal.CTRL_BREAK_EVENT
        self._process.send_signal(sigterm)
        try:
            self._process.wait(4)
        except subprocess.TimeoutExpired:
            self._process.terminate()

    def execute(
        self,
        arguments: Iterable[str] | None = None,
        input_stream: bytes | IO[bytes] | None = None,
    ) -> bool:
        args = list(arguments or [])
        if not args:
            return False
        self._canceled = False
        self._cancel_event.clear()
        try:
            with self._running_cond:
                self._process = StreamUtils.create_subprocess(
                    args,
                    # bufsize=0,
                    stdin=subprocess.PIPE if (input_stream is not None) else None,
                    # stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                self.emit("started")

                for line in StreamUtils.readlines_from_stream(
                    StreamUtils.wrap_io(self._process.stderr)
                ):
                    self._handle_stderr(line)
                    if self._cancel_event.is_set():
                        self._process.terminate()
                        self._canceled = True
                        self._cancel_event.clear()
                        break
                    time.sleep(0.01)
            # running_cond
        finally:
            self._process.wait()
            result = self._process.returncode == 0
            if self._canceled:
                self.emit("canceled")
            elif result is False:
                self.emit("terminated")
            else:
                self.emit("finished")
            return result

    def get_basic_info(self, filename: Path) -> dict:
        with self._running_cond:
            self._process = StreamUtils.create_subprocess(
                self._executable,
                "-i",
                str(filename),
                stderr=subprocess.PIPE,
            )

            stream = StreamUtils.wrap_io(self._process.stderr)
            result = self._parse_basic_info_from_stream(stream)
            self._process.wait()
            return result
        # running_cond

    def _parse_basic_info_from_stream(self, input_stream: IO[bytes]) -> dict:
        result = {}
        streams = []
        for line in StreamUtils.readlines_from_stream(input_stream):
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
        if len(streams) > 0:
            result["streams"] = streams
        return result
