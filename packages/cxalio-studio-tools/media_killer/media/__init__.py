"""media_killer 共享底座。

本包承载可被其他工具复用的通用转码契约与执行能力，当前包含：
- Mission 契约（Mission、InputSpec、OutputSpec）
- 单 Mission 执行单元（MissionExecutor、MissionPretender、MissionResult、事件常量）
- MissionHQ 异步任务执行底座（MissionHQ、ProgressSnapshot、ExecutorFactory 等）
- 媒体元数据探测（MediaProber、MediaDB、MediaInfo）

未来 ffpretty 等工具可从 ``media_killer.media`` 导入这些符号。
"""

from .executor import (
    ExecutorStatus,
    FfmpegErrorInfo,
    FileLogType,
    MissionExecutor,
    MissionResult,
)
from .executor_factory import ExecutorFactory
from .executor_scheduler import ExecutorScheduler
from .media_db import MediaDB
from .media_info import MediaInfo, StreamInfo
from .media_prober import MediaProber
from .mission import InputSpec, Mission, OutputSpec
from .mission_hq import MissionHQ, ProgressSnapshot
from .pretender import MissionPretender
from .task_progress import TaskProgress
from .total_progress import TotalProgress
from .whisperer import Whisperer

__all__ = [
    "ExecutorFactory",
    "ExecutorScheduler",
    "ExecutorStatus",
    "FfmpegErrorInfo",
    "FileLogType",
    "InputSpec",
    "MediaDB",
    "MediaInfo",
    "MediaProber",
    "Mission",
    "MissionExecutor",
    "MissionHQ",
    "MissionPretender",
    "MissionResult",
    "OutputSpec",
    "ProgressSnapshot",
    "StreamInfo",
    "TaskProgress",
    "TotalProgress",
    "Whisperer",
]
