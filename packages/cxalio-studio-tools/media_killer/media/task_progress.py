"""子进度条管理器。

为每个正在执行的 Mission 维护一个 Rich Progress 子 task，
通过订阅 executor 的 PROGRESS_UPDATED 和 STATUS_UPDATED 事件实时更新。

职责单一：管理子进度条的创建、更新和销毁。不参与总进度计算。
"""

from typing import TYPE_CHECKING

from rich.progress import TaskID

from cx_studio.ffmpeg import FFmpegCodingInfo

from .executor import PROGRESS_UPDATED, STATUS_UPDATED, MissionExecutor

if TYPE_CHECKING:
    from .mission_hq import MissionHQ


class TaskProgress:
    """子进度条管理器——事件驱动，非轮询。

    每个 executor 一个子进度条，显示格式：
    ``[cx.debug][⟨index⟩/⟨total⟩][/] [cx.mk.mission.name]⟨name⟩[/]``

    通过 STATUS_UPDATED 事件自动更新转码速度指示器（如 ``[3.21x]``）。

    Attributes:
        _hq: 反向引用 MissionHQ，访问 progress 组件
        _bars: executor_id → Rich Progress TaskID 映射
        _last_completed: 上次更新的 completed 值，用于去重
        _last_total: 上次更新的 total 值，用于去重
    """

    def __init__(self, hq: "MissionHQ"):
        """初始化子进度条管理器。

        Args:
            hq: MissionHQ 实例引用
        """
        self._hq = hq
        self._bars: dict[int, TaskID] = {}
        self._last_completed: dict[int, float] = {}
        self._last_total: dict[int, float] = {}

    def watch(self, executor: MissionExecutor, index: int) -> None:
        """开始追踪一个 executor 的进度。

        立即创建 Rich Progress 子 task（非懒创建），
        并订阅 executor 的 PROGRESS_UPDATED 和 STATUS_UPDATED 事件。

        Args:
            executor: 要追踪的 MissionExecutor 实例
            index: mission 在 _all_missions 列表中的索引（0-based）
        """
        assert self._hq._progress is not None
        eid = executor.executor_id
        status = executor.status
        total = len(self._hq._all_missions)
        name = status.mission_name
        # 创建进度条（立即显示）
        tid = self._hq._progress.add_task(
            f"[cx.debug][{index + 1}/{total}][/] [cx.mk.mission.name]{name}[/]",
            total=None,
        )
        self._bars[eid] = tid
        # 订阅事件（闭包捕获 eid / index / total / name）
        executor.on(
            PROGRESS_UPDATED,
            lambda current, t: self._on_progress(eid, current, t),
        )
        executor.on(
            STATUS_UPDATED,
            lambda ci: self._on_status(eid, ci, index, total, name),
        )

    def forget(self, executor: MissionExecutor) -> None:
        """停止追踪并移除对应的进度条。

        在 executor 执行完成（成功/失败/取消）后调用。
        从 Rich Progress 中移除子 task 并清理内部状态。

        Args:
            executor: 已完成的 MissionExecutor 实例
        """
        assert self._hq._progress is not None
        eid = executor.executor_id
        tid = self._bars.pop(eid, None)
        if tid is not None:
            self._hq._progress.remove_task(tid)
        self._last_completed.pop(eid, None)
        self._last_total.pop(eid, None)

    def _on_progress(self, eid: int, current, total_time) -> None:
        """PROGRESS_UPDATED 事件处理器。

        更新子进度条的 completed/total 字段。使用 _last_* 字典去重——
        仅在值实际变化时才调用 progress.update()，避免 Rich 内部重绘开销。

        Args:
            eid: executor 的 ID
            current: CxTime 当前进度
            total_time: CxTime | None 预估总时长
        """
        assert self._hq._progress is not None
        tid = self._bars.get(eid)
        if tid is None:
            return
        new_c = current.total_seconds
        new_t = (
            total_time.total_seconds
            if total_time and total_time.total_seconds > 0
            else None
        )
        if self._last_completed.get(eid) != new_c:
            self._hq._progress.update(tid, completed=new_c)
            self._last_completed[eid] = new_c
        if new_t is not None and self._last_total.get(eid) != new_t:
            self._hq._progress.update(tid, total=new_t)
            self._last_total[eid] = new_t

    def _on_status(
        self,
        eid: int,
        coding_info: FFmpegCodingInfo,
        index: int,
        total: int,
        name: str,
    ) -> None:
        """STATUS_UPDATED 事件处理器。

        更新进度条描述文本，显示当前转码速率（如 ``[3.21x]``）。
        仅在速率 > 0 时更新（起始阶段 coding_info 可能未初始化）。

        Args:
            eid: executor 的 ID
            coding_info: FFmpeg 帧级状态快照
            index: mission 在 _all_missions 中的 0-based 索引
            total: _all_missions 中 mission 总数
            name: mission 名称（源文件名，不含扩展名）
        """
        assert self._hq._progress is not None
        tid = self._bars.get(eid)
        if tid is None:
            return
        speed = coding_info.current_speed
        if speed > 0:
            self._hq._progress.update(
                tid,
                description=(
                    f"[cx.debug][{index + 1}/{total}] [{speed:.2f}x][/]"
                    f" [cx.mk.mission.name]{name}[/]"
                ),
            )
