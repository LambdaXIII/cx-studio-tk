"""Executor 模块 - 单 Mission 执行单元。

提供 MissionExecutor、MissionResult 和事件名常量。
"""

from .events import (
    CANCELED,
    FAILED,
    FINISHED,
    PROGRESS_UPDATED,
    STARTED,
    STATUS_UPDATED,
    VERBOSE,
)
from .executor import MissionExecutor
from .result import MissionResult

__all__ = [
    "CANCELED",
    "FAILED",
    "FINISHED",
    "MissionExecutor",
    "MissionResult",
    "PROGRESS_UPDATED",
    "STARTED",
    "STATUS_UPDATED",
    "VERBOSE",
]
