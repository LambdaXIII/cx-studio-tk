"""MissionExecutor 事件名常量。

集中定义事件名称字符串，避免调用点硬编码。
"""

# FFmpeg 进程已启动
STARTED: str = "started"
# 进度更新：(current: CxTime, total: CxTime | None)
PROGRESS_UPDATED: str = "progress_updated"
# 帧级状态更新：(coding_info: FFmpegCodingInfo)
STATUS_UPDATED: str = "status_updated"
# 转码成功完成
FINISHED: str = "finished"
# 转码失败：(reason: str)
FAILED: str = "failed"
# 被外部取消
CANCELED: str = "canceled"
# FFmpeg 原始 stderr 行：(line: str)
VERBOSE: str = "verbose"
