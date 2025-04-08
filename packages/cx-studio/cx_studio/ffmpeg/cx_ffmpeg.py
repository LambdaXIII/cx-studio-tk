from codecs import ignore_errors
import datetime
from .cx_ffmpeg_exceptions import FFmpegOutputParseError
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


class FFmpeg:
    def __init__(self, ffmpeg_bin: str | None) -> None:
        self._ffmpeg_bin = ffmpeg_bin or "ffmpeg"
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
        result = {}

        args = f"-hide_banner -i {source}".split(" ")

        with self._running_cond:
            process = subprocess.Popen(
                args, executable=self._ffmpeg_bin, stderr=subprocess.PIPE
            )
            process.wait()

        output = process.stderr.read().decode("utf-8") if process.stderr else None
        if output is None:
            raise FFmpegOutputParseError("No output from ffmpeg", output)

        streams = []
        for line in output.split("\n"):
            input_match = re.match(r"Input #0, (.+), from '(.+)':", line)
            if input_match:
                result["format_name"] = input_match.group(1)
                result["file_name"] = input_match.group(2)
                continue

            time_match = re.match(
                r"Duration: (.+), start: (.+), bitrate: (\d+(\.\d+)?\s?\w+/s)", line
            )
            if time_match:
                result["duration"] = CxTime.from_timestamp(time_match.group(1))
                result["start_time"] = CxTime.from_seconds(float(time_match.group(2)))
                result["bitrate"] = FileSize.from_string(time_match.group(3))
                continue

            streams_match = re.match(r"Stream #0:\d+\s+", line)
            if streams_match:
                streams.append(line)
                continue

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

    def run(self, arguments: str | list) -> bool:
        args = arguments.split(" ") if isinstance(arguments, str) else arguments

        with self._running_cond:
            process = subprocess.Popen(
                args, executable=self._ffmpeg_bin, stderr=subprocess.PIPE, text=True
            )

            basic_process_info = FFmpegProcessInfo(
                bin=self._ffmpeg_bin, args=args, start_time=datetime.now()
            )
            self.__emit_signal("started", basic_process_info)

            for line in process.stderr:  # type:ignore
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
                        "status_updated", basic_process_info, coding_status
                    )

                if self._cancel_event.is_set():
                    process.communicate("q")
                    process.wait(3)
                    if process.returncode == 0:
                        process.kill()
                        self.__emit_signal("canceled", basic_process_info)
                    break

            process.wait()

        basic_process_info = replace(basic_process_info, end_time=datetime.now())
        self.__emit_signal("finished", basic_process_info)
        return process.returncode == 0
