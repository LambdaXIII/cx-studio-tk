"""media_killer 共享底座。

本包承载可被其他工具复用的通用转码契约与执行能力，当前包含：
- Mission 契约（Mission、InputSpec、OutputSpec）
- 单 Mission 执行单元（MissionExecutor、MissionPretender、MissionResult、事件常量）
- 媒体元数据探测（MediaProber、MediaDB、MediaInfo）

未来 ffpretty 等工具可从 `media_killer.media` 导入这些符号。
"""

from .executor import (
    ARGS_BUILT,
    CANCELED,
    CANCELING,
    COMMIT_RENAMED,
    ExecutorStatus,
    FAILED,
    FFMPEG_FAILED,
    FFMPEG_FINISHED,
    FFMPEG_STARTED,
    FINISHED,
    MissionExecutor,
    MissionResult,
    PROGRESS_UPDATED,
    SKIPPED,
    STARTED,
    STATUS_UPDATED,
    VERBOSE,
)
from .media_db import MediaDB
from .media_info import MediaInfo
from .media_prober import MediaProber
from .mission import InputSpec, Mission, OutputSpec
from .pretender import MissionPretender

__all__ = [
    "ARGS_BUILT",
    "CANCELED",
    "CANCELING",
    "COMMIT_RENAMED",
    "ExecutorStatus",
    "FAILED",
    "FFMPEG_FAILED",
    "FFMPEG_FINISHED",
    "FFMPEG_STARTED",
    "FINISHED",
    "InputSpec",
    "MediaDB",
    "MediaInfo",
    "MediaProber",
    "Mission",
    "MissionExecutor",
    "MissionPretender",
    "MissionResult",
    "OutputSpec",
    "PROGRESS_UPDATED",
    "SKIPPED",
    "STARTED",
    "STATUS_UPDATED",
    "VERBOSE",
]
