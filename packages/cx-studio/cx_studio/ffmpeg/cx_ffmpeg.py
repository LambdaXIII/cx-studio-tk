from codecs import ignore_errors
from .cx_ffmpeg_exceptions import FFmpegOutputParseError
from .cx_ffmpeg_infos import FFmpegFormatInfo

from pathlib import Path
from cx_studio.core import FileSize, CxTime
from collections import defaultdict
import subprocess
import re


class FFmpeg:
    def __init__(self, ffmpeg_bin: str | None) -> None:
        self._ffmpeg_bin = ffmpeg_bin or "ffmpeg"
        self._event_handlers = defaultdict(list)

    def get_basic_info(self, source: str | Path) -> dict:
        result = {}

        args = f"-hide_banner -i {source}".split(" ")
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
