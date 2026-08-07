"""总进度条管理器。

后台协程以 2Hz 频率轮询 MissionHQ.progress_snapshot()，
更新 Rich Progress 中的总进度条。

职责单一：轮询 + 更新总进度栏。不干预子进度条。
"""

import asyncio
import time
from typing import TYPE_CHECKING

from cx_wealthy import rich_types as r

from media_killer.i18n import _

if TYPE_CHECKING:
    from .mission_hq import MissionHQ


class TotalProgress:
    """总进度条管理器。

    使用时间网格对齐轮询（非固定间隔 sleep），避免漂移。
    轮询间隔 0.5s（2Hz），可在 Rich 60fps 刷新率下保持平滑。

    Attributes:
        INTERVAL: 轮询间隔（秒），常量 0.5
        _hq: 反向引用 MissionHQ
        _bar: Rich Progress 总进度 task ID，None 表示未创建
    """

    INTERVAL = 0.5  # 2 Hz

    def __init__(self, hq: "MissionHQ"):
        """初始化。

        Args:
            hq: MissionHQ 实例引用
        """
        self._hq = hq
        self._bar: r.TaskID | None = None
        self._progress: r.Progress | None = None

    async def run(self) -> None:
        """后台协程：对齐时间网格轮询，超时跳过不补。

        终止方式：由 MissionHQ.run() 通过 task.cancel() 取消。
        创建总进度条，开始轮询，取消信号到来时清理资源。
        """
        self._progress = self._hq._progress
        if self._progress is None:
            return

        self._bar = self._progress.add_task(_("总进度"), total=None)
        next_tick = time.monotonic() + self.INTERVAL

        try:
            while True:
                now = time.monotonic()
                if now < next_tick:
                    # 对齐时间网格：sleep 到下一个 tick 时刻
                    await asyncio.sleep(next_tick - now)
                next_tick += self.INTERVAL
                self._sync()
        except asyncio.CancelledError:
            pass
        finally:
            self._finalize()

    def _sync(self) -> None:
        """单次轮询：获取进度快照并更新 Rich Progress。

        仅在 total > 0 时更新——任务列表为空时进度条保持空白。
        """
        snap = self._hq.progress_snapshot()
        if snap.total > 0 and self._bar is not None and self._progress is not None:
            self._progress.update(
                self._bar,
                completed=snap.completed,
                total=snap.total,
            )

    def _finalize(self) -> None:
        """清理资源：从 Rich Progress 中移除总进度条。

        在 run() 的 finally 块中调用，确保任务取消时资源正确释放。
        """
        if self._bar is not None and self._progress is not None:
            self._progress.remove_task(self._bar)
            self._bar = None
