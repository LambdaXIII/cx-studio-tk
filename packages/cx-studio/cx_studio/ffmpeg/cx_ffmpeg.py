from codecs import ignore_errors
from collections.abc import Iterable
import datetime
from .cx_ffmpeg_exceptions import FFmpegOutputParseError, NoFFmpegExecutableError
from .cx_ffmpeg_infos import FFmpegCodingInfo, FFmpegFormatInfo, FFmpegProcessInfo

from pathlib import Path
from cx_studio.core import FileSize, CxTime
from collections import defaultdict
import subprocess
import re
from functools import wraps

from datetime import datetime
from dataclasses import replace
import threading
from cx_studio.path_expander import CmdFinder


class FFmpeg:
    def __init__(self, ffmpeg_executable: str | None = None) -> None:
        self._executable = CmdFinder.which(ffmpeg_executable or "ffmpeg")
        self._signal_handlers = defaultdict(list)
        self._signal_lock = threading.RLock()
        self._cancel_event = threading.Event()
        self._running_lock = threading.Lock()
        self._running_cond = threading.Condition(self._running_lock)

    def cancel(self):
        self._cancel_event.set()
        with self._running_cond:
            self._running_cond.notify_all()
        self._cancel_event.clear()

    def is_running(self):
        return self._running_lock.locked()

    def get_basic_info(self, source: str | Path) -> dict:
        if not self._executable:
            raise NoFFmpegExecutableError("No ffmpeg executable found.")

        result = {}
        streams = []

        # args = f"-hide_banner -i {source}".split(" ")
        args = [self._executable, "-hide_banner", "-i", source]

        with self._running_cond:
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
        # condition
        if len(streams) > 0:
            result["streams"] = streams
        return result

    def __emit_signal(self, signal: str, *args, **kwargs):
        if signal not in self._signal_handlers:
            return
        with self._signal_lock:
            for handler in self._signal_handlers[signal]:
                handler(*args, **kwargs)

    def on(self, signal: str):
        def deco(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            with self._signal_lock:
                self._signal_handlers[signal].append(wrapper)
            return wrapper

        return deco

    def run(self, arguments: str | list | Iterable) -> bool:
        if not self._executable:
            raise NoFFmpegExecutableError("No ffmpeg executable found.")

        args = [
            str(x)
            for x in (arguments.split(" ") if isinstance(arguments, str) else arguments)
        ]
        args.insert(0, str(self._executable))

        with self._running_cond:

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
                self.__emit_signal("started", basic_process_info)

                for line in process.stderr or []:
                    if basic_process_info.media_duration is None:
                        match = re.match(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", line)
                        if match:
                            duration = CxTime.from_timestamp(match.group(1))
                            basic_process_info = replace(
                                basic_process_info, media_duration=duration
                            )

                    line = line.strip()
                    if line.startswith("frame="):
                        coding_status = FFmpegCodingInfo.parse_status_line(line)
                        self.__emit_signal(
                            "progress_updated", basic_process_info, coding_status
                        )

                    if self._cancel_event.is_set():
                        process.communicate("q")
                        process.wait(3)
                        if process.returncode == 0:
                            process.kill()
                            self.__emit_signal("canceled", basic_process_info)
                        break
                # for
                process.wait()
            # process
        # condition
        basic_process_info = replace(basic_process_info, end_time=datetime.now())
        self.__emit_signal("finished", basic_process_info)
        return process.returncode == 0
