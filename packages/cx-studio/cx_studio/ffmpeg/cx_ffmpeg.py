from copy import copy
import concurrent.futures as con_futures
import io
import signal
import subprocess
import sys
import threading
from collections.abc import Iterable
from copy import copy
from pathlib import Path
from typing import IO

from pyee import EventEmitter

from cx_studio.core import CxTime, FileSize
from cx_studio.filesystem import CmdFinder
from cx_studio.iotools import StreamUtils
from .cx_ff_errors import *
from .cx_ff_infos import FFmpegCodingInfo


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

    def _redirect_stdin(self, stream: IO[bytes] | None):
        if stream is None:
            return

        assert self._process.stdin is not None

        for chunk in StreamUtils.read_stream(stream, io.DEFAULT_BUFFER_SIZE):
            self._process.stdin.write(chunk)
        self._process.stdin.flush()
        self._process.stdin.close()

    def _read_stdout(self) -> bytes:
        assert self._process.stdout is not None

        buffer = bytearray()
        for chunk in StreamUtils.read_stream(
            self._process.stdout, io.DEFAULT_BUFFER_SIZE
        ):
            buffer.extend(chunk)

        self._process.stdout.close()
        return bytes(buffer)

    def _handle_stderr(self):
        assert self._process.stderr is not None
        line = b""
        for line in StreamUtils.readlines_from_stream(self._process.stderr):
            line_str = line.decode("utf-8", errors="ignore")
            self.emit("verbose", line_str)

            conding_info_dict = FFmpegCodingInfo.parse_status_line(line_str)

            self._coding_info.update(**conding_info_dict)

            if "current_time" in conding_info_dict or "total_time" in conding_info_dict:
                self.emit(
                    "progress_updated",
                    self._coding_info.current_time,
                    self._coding_info.total_time,
                )

            if "current_frame" in conding_info_dict:
                self.emit("status_updated", copy(self._coding_info))

        self._process.stderr.close()
        return line.decode()

    def _handle_cancel_event(self):
        while self._process.poll() is None:
            if self._cancel_event.wait(0.1):
                self._canceled = True
                self._process.terminate()
                self._process.wait()
                self._cancel_event.clear()
                break

    def execute(
        self,
        arguments: Iterable[str] | None = None,
        input_stream: IO[bytes] | None = None,
    ) -> bool:
        with self._running_cond:
            self._canceled = False
            self._cancel_event.clear()

            try:
                args = [self._executable, *(arguments or [])]

                self._process = StreamUtils.create_subprocess(
                    args,
                    bufsize=0,
                    stdin=subprocess.PIPE if input_stream is not None else None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                self.emit("started")

                if input_stream is not None:
                    input_stream = StreamUtils.wrap_io(input_stream)

                with con_futures.ThreadPoolExecutor() as executor:
                    futures = [
                        executor.submit(self._handle_stderr),
                        executor.submit(self._redirect_stdin, input_stream),
                        executor.submit(self._read_stdout),
                        executor.submit(self._handle_cancel_event),
                        executor.submit(self._process.wait),
                    ]

                    done, pending = con_futures.wait(
                        futures,
                        timeout=None,
                        return_when=con_futures.FIRST_EXCEPTION,
                    )

                    for future in done:
                        exs = future.exception()
                        if exs is not None:
                            self._process.terminate()
                            con_futures.wait(pending)
                            raise exs
            except:
                pass
            # finally:
            self._process.wait()
            result = self._process.returncode == 0
            if self._canceled:
                self.emit("canceled")
            elif result is False:
                self.emit("terminated")
            else:
                self.emit("finished")
            return result

        # running_cond
