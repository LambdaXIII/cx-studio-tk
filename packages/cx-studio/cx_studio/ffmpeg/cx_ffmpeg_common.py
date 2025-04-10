from collections.abc import Callable
from typing import Literal

from .cx_ffmpeg_infos import FFmpegCodingInfo, FFmpegProcessInfo

FFmpegEventLiteral = Literal[
    "started", "finished", "canceled", "progress_updated", "verbose"
]

FFmpegEventHandler = Callable[[FFmpegCodingInfo | None, FFmpegProcessInfo], None]
