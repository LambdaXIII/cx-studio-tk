import json
import subprocess
from pathlib import Path

from cx_studio.path_expander import CmdFinder
from cx_studio.utils import PathUtils
from .cx_ffmpeg_exceptions import FFmpegOutputParseError, NoFFmpegExecutableError
from .cx_ffmpeg_infos import FFmpegFormatInfo


class FFprobe:
    def __init__(self, ffprobe_executable: str | Path | None = None) -> None:
        self._executable = CmdFinder.which(ffprobe_executable or "ffprobe")

    def get_format_info(self, source: str | Path) -> FFmpegFormatInfo:
        if not self._executable:
            raise NoFFmpegExecutableError("No ffprobe executable found.")

        source = PathUtils.get_posix_path(Path(source).resolve())

        args = [
            self._executable,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(source),
        ]

        with subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        ) as process:
            process.wait()
            output_str = process.stdout.read() if process.stdout else ""

            if not output_str:
                raise FFmpegOutputParseError("No output", output_str)

        data = json.loads(output_str).get("format", {})
        return FFmpegFormatInfo.from_format_dict(data)
