"""ffpretty 通用能力面，对外提供面。

承载 ffpretty 的执行核心能力：Mission 参数模型、MissionExecutor 执行核心、
媒体元数据探测（MediaProber/MediaDB/MediaInfo）等。工具间组合只允许
指向本包的 common 出口（可到 `ffpretty.common.<module>`）。
"""

from .executor import (
    ExecutorStatus,
    FfmpegErrorInfo,
    FileLogType,
    MissionExecutor,
    MissionFailureInfo,
    MissionResult,
)
from .media_db import MediaDB
from .media_info import MediaInfo, StreamInfo
from .media_prober import MediaProber
from .mission import (
    FfmpegOption,
    InputSpec,
    Mission,
    OutputSpec,
    iter_option_tokens,
    options_from_flat,
)
from .pretender import MissionPretender
from .whisperer import Whisperer

__all__ = [
    "ExecutorStatus",
    "FfmpegErrorInfo",
    "FfmpegOption",
    "FileLogType",
    "InputSpec",
    "MediaDB",
    "MediaInfo",
    "MediaProber",
    "Mission",
    "MissionExecutor",
    "MissionFailureInfo",
    "MissionPretender",
    "MissionResult",
    "OutputSpec",
    "StreamInfo",
    "Whisperer",
    "iter_option_tokens",
    "options_from_flat",
]
