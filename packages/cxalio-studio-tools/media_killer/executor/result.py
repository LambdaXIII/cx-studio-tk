"""Mission 执行结果枚举。"""

from enum import Enum


class MissionResult(Enum):
    """Mission 执行结果。

    Attributes:
        SUCCESS: 转码成功完成
        FAILED: 转码失败（校验失败或 FFmpeg 异常退出）
        CANCELED: 被外部取消
    """

    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"
