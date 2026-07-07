"""模拟运行执行单元。

本模块提供模拟运行版本的执行单元，用于 ``-p/--pretend`` 模式。
继承 ``MissionExecutor``，覆盖 ``execute()`` 使用虚拟延时模拟转码进度。
不调用 FFmpeg、不创建目录、不写临时文件。

cancel() 和 garbage_files 共享父类实现（_garbage_files 始终为空——不创建临时文件）。
"""

import asyncio
from cx_tools.i18n import _

from cx_studio.core.cx_time import CxTime

from .executor import (
    CANCELED,
    CANCELING,
    FAILED,
    FINISHED,
    MissionExecutor,
    MissionResult,
    PROGRESS_UPDATED,
    SKIPPED,
    STARTED,
)
from .mission import Mission


class MissionPretender(MissionExecutor):
    """模拟运行执行单元。

    继承 ``MissionExecutor``，覆盖 ``execute()`` 使用虚拟延时模拟转码进度。
    不调用 FFmpeg、不创建目录、不写临时文件。
    cancel() 和 garbage_files 共享父类实现。

    事件：
        started, progress_updated, finished, failed, canceled, skipped
    """

    def __init__(
        self,
        mission: Mission,
        duration: CxTime | None = None,
    ) -> None:
        """初始化 MissionPretender。

        Args:
            mission: 要模拟执行的 Mission
            duration: 模拟转码时长。若为 None，使用默认 60 秒。
        """
        super().__init__(mission)
        self._duration = duration or CxTime.from_seconds(60.0)

    async def execute(self) -> MissionResult:
        """模拟执行 Mission。

        流程：校验 → 跳过检查 → 模拟进度 → 完成。

        Returns:
            MissionResult: 执行结果（SUCCESS/FAILED/CANCELED/SKIPPED）
        """
        # 校验（共享父类 _validate()）
        try:
            self._validate()
        except Exception as e:
            self._failure_reason = str(e)
            self.emit(FAILED)
            return MissionResult.FAILED

        # 覆盖检查：target 已存在且 overwrite=False → 跳过
        if not self._mission.overwrite:
            existing = [
                s.filename for s in self._mission.outputs if s.filename.exists()
            ]
            if existing:
                self._skipped_targets = [str(e) for e in existing]
                self.emit(SKIPPED)
                return MissionResult.SKIPPED

        # 模拟执行（不创建目录、不写临时文件）
        self.emit(STARTED)

        total_ms = self._duration.total_milliseconds
        segments = 20
        segment_ms = max(1, total_ms // segments)

        try:
            for i in range(1, segments + 1):
                if self._cancel_event.is_set():
                    self._cancel_reason = _("用户中断")
                    self.emit(CANCELING)
                    self.emit(CANCELED)
                    return MissionResult.CANCELED

                current = CxTime(i * segment_ms)
                total = CxTime(total_ms)
                self.emit(PROGRESS_UPDATED, current, total)
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            self._cancel_reason = _("调度器强制取消")
            self.emit(CANCELING)
            return MissionResult.CANCELED

        self.emit(FINISHED)
        return MissionResult.SUCCESS
