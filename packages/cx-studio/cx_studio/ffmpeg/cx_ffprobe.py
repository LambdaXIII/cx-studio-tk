from pathlib import Path
from .cx_ffmpeg_infos import FFmpegFormatInfo
from cx_studio.core import CxTime, FileSize
import subprocess
from .cx_ffmpeg_exceptions import FFmpegOutputParseError
import json


class FFprobe:
    def __init__(self, ffprobe_bin: str | None) -> None:
        self._ffprobe_bin = ffprobe_bin or "ffprobe"

    def get_format_info(self, source: str | Path) -> FFmpegFormatInfo:
        cmd = "-v quiet -print_format json -show_format"
        source = Path(source).resolve()

        process = subprocess.Popen(
            [cmd, str(source)],
            executable=self._ffprobe_bin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.wait()
        output_str = process.stdout.read().decode("utf-8") if process.stdout else None
        if output_str is None:
            raise FFmpegOutputParseError("No output", output_str)

        data = json.loads(output_str).get("format", {})
        return FFmpegFormatInfo.from_format_dict(data)
