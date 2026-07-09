"""Mission 批量调度器。

管理一批 Mission 的并发执行与两段式中断分发。当前实现使用
``asyncio.Semaphore`` 控制并发度（无 queue 数据结构），所有 Mission
一次性创建为 ``asyncio.Task``，Semaphore 控制同时运行的 task 数量。

中断语义（两段式）：
- 第一次 Ctrl+C：Application 回调调用 ``scheduler.cancel_running()``，
  对所有正在运行的 executor 调用 ``cancel()``。executor 在自身轮询循环
  中检测到 ``_cancel_event`` 后自行中止。pending 任务不受影响。
- 第二次 Ctrl+C（3 秒内）：Application 回调调用 ``scheduler.cancel_all()``，
  取消所有任务（pending + running）。pending task 获得 semaphore 后检查
  ``_cancel_all_event`` 直接返回 CANCELED，running task 被
  ``task.cancel()`` 取消，executor 的 ``asyncio.CancelledError``
  处理后返回 CANCELED。

事件（聚合级别，将 executor 的作业级事件映射到调度器的任务级事件）。
所有 ``mission_*`` 事件参数统一为 ``(index: int, status: ExecutorStatus)``，
接收端从 status 快照中拉取上下文数据。流式数据事件
（mission_progress_updated / mission_status_updated / mission_verbose）
保持原有参数不变。

| 事件名 | 参数 | 来源 |
|---|---|---|
| ``mission_started`` | ``index: int, status: ExecutorStatus`` | scheduler 自有 |
| ``mission_progress_updated`` | ``index: int, current: CxTime, total: CxTime | None`` | 中继 |
| ``mission_status_updated`` | ``index: int, coding_info: FFmpegCodingInfo`` | 中继 |
| ``mission_failed`` | ``index: int, status: ExecutorStatus`` | 中继自 executor FAILED |
| ``mission_canceled`` | ``index: int, status: ExecutorStatus`` | 中继自 executor CANCELED |
| ``mission_canceling`` | ``index: int, status: ExecutorStatus`` | 中继自 executor CANCELING |
| ``mission_skipped`` | ``index: int, status: ExecutorStatus`` | 中继自 executor SKIPPED |
| ``mission_verbose`` | ``index: int, line: str`` | 中继自 executor VERBOSE |
| ``mission_args_built`` | ``index: int, status: ExecutorStatus`` | 中继 |
| ``mission_commit_renamed`` | ``index: int, status: ExecutorStatus`` | 中继 |
| ``mission_ffmpeg_started`` | ``index: int, status: ExecutorStatus`` | 中继 |
| ``mission_ffmpeg_finished`` | ``index: int, status: ExecutorStatus`` | 中继 |
| ``mission_ffmpeg_failed`` | ``index: int, status: ExecutorStatus`` | 中继 |
| ``mission_finished`` | ``index: int, status: ExecutorStatus`` | scheduler 自有 |
| ``all_finished`` | ``()`` | scheduler 自有，通过 scheduler.results 拉取 |
| ``scheduler_canceling`` | ``()`` | scheduler 级 CANCELING 信号 |
"""

import asyncio
from dataclasses import dataclass
from collections.abc import Callable, Iterable
from pathlib import Path

from pyee.asyncio import AsyncIOEventEmitter

from rich.progress import TaskID

from cx_tools.i18n import _

from ..media.executor import (
    ARGS_BUILT,
    CANCELED,
    CANCELING,
    COMMIT_RENAMED,
    FAILED,
    FFMPEG_FAILED,
    FFMPEG_FINISHED,
    FFMPEG_STARTED,
    FINISHED,
    PROGRESS_UPDATED,
    SKIPPED,
    STARTED,
    STATUS_UPDATED,
    VERBOSE,
    MissionExecutor,
    ExecutorStatus,
    MissionResult,
)
from ..media.mission import Mission
from ..media.pretender import MissionPretender
from ..appenv import appenv

# scheduler 中继的 executor 事件列表。
# 排除 STARTED 和 FINISHED：scheduler 在 executor.execute() 前后
# 自行发射 mission_started / mission_finished（携带 Mission / MissionResult），
_RELAY_EVENTS: tuple[str, ...] = (
    PROGRESS_UPDATED,
    STATUS_UPDATED,
    FAILED,
    CANCELED,
    CANCELING,
    SKIPPED,
    VERBOSE,
    ARGS_BUILT,
    COMMIT_RENAMED,
    FFMPEG_STARTED,
    FFMPEG_FINISHED,
    FFMPEG_FAILED,
)


@dataclass
class SchedulerStatus:
    """scheduler 运行时动态信息的只读快照。"""

    total_missions: int  # 总任务数
    completed_count: int  # 已完成数（含成功/失败/取消/跳过）
    running_count: int  # 正在执行数
    pending_count: int  # 等待槽位数
    canceled_by_interrupt: bool  # 是否因二次中断触发 cancel_all


# scheduler 识别到强制中断信号，即将取消所有任务：()
# 在 cancel_all() 或 _watch_cancel_all 触发时发射。
# 与 all_finished 的区别：CANCELING = "正在取消全部"，all_finished = "全部结束"。
SCHEDULER_CANCELING: str = "scheduler_canceling"


class MissionScheduler(AsyncIOEventEmitter):
    """Mission 批量调度器。

    Args:
        missions: 待执行的 Mission 列表
        max_workers: 最大并发数
        executor_factory: 工厂函数，(Mission) -> MissionExecutor | MissionPretender。
            每次调度一个 Mission 时调用。
    """

    def __init__(
        self,
        missions: Iterable[Mission],
        max_workers: int = 1,
        executor_factory: (
            Callable[[Mission], MissionExecutor | MissionPretender] | None
        ) = None,
    ) -> None:
        super().__init__()
        self._missions = list(missions)
        self._max_workers = max(1, max_workers)
        self._executor_factory: Callable[[Mission], MissionExecutor | MissionPretender]
        if executor_factory is None:
            self._executor_factory = lambda m: MissionExecutor(m)
        else:
            self._executor_factory = executor_factory
        self._cancel_all_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        self._completed_count: int = 0
        self._running_count: int = 0
        self._canceled_by_interrupt: bool = False
        self._results: dict[int, MissionResult] = {}
        self._running_executors: dict[int, MissionExecutor | MissionPretender] = {}
        # 每个 mission 最终确定的 total_time 缓存。
        # 在 mission 完成时从 coding_info.total_time 记录（若可用），
        # 确保已结束和运行中的任务使用同一 total 来源，避免跳变。
        self._mission_total_cache: dict[int, float] = {}

    @property
    def status(self) -> SchedulerStatus:
        """返回当前运行时状态的只读快照。"""
        return SchedulerStatus(
            total_missions=len(self._missions),
            completed_count=self._completed_count,
            running_count=self._running_count,
            pending_count=max(
                0, len(self._missions) - self._completed_count - self._running_count
            ),
            canceled_by_interrupt=self._canceled_by_interrupt,
        )

    @property
    def results(self) -> dict[int, MissionResult]:
        """返回所有已完成的 Mission 结果。key = index, value = result。"""
        return dict(self._results)

    def cancel_running(self) -> None:
        """取消所有正在运行的 executor，pending 任务不受影响。

        供 Application 在 ``first_triggered`` 时调用。
        对每个 running executor 调用 ``executor.cancel()``，
        executor 在自身轮询循环中检测到后自行中止。
        """
        for executor in self._running_executors.values():
            executor.cancel()

    def cancel_all(self) -> None:
        """取消所有任务（pending + running）。

        供 Application 在 ``second_triggered`` 时直接调用。
        幂等：若已触发过 cancel_all，后续调用为 no-op。
        """
        if self._cancel_all_event.is_set():
            return
        self._canceled_by_interrupt = True
        self.emit(SCHEDULER_CANCELING)
        self._cancel_all_event.set()
        for task in self._tasks:
            if not task.done():
                task.cancel()

    async def run(
        self,
        overall_task_id: TaskID | None = None,
        mission_totals: list[float] | None = None,
    ) -> list[MissionResult]:
        """启动批量调度。
        所有 Mission 一次性创建 asyncio.Task，Semaphore 控制并发度。

        Args:
            overall_task_id: 总体进度条 TaskID（可选）。提供时启动轮询协程。
            mission_totals: 每项任务的总时长（秒），与 overall_task_id 配对使用。

        Returns:
            list[MissionResult]: 每个 Mission 的执行结果（顺序与输入一致）
        """
        sem = asyncio.Semaphore(self._max_workers)
        self._cancel_all_event = asyncio.Event()
        self._tasks = [
            asyncio.create_task(self._run_one(i, mission, sem))
            for i, mission in enumerate(self._missions)
        ]
        # 总体进度轮询 task（生命周期与 run() 匹配）
        if overall_task_id is not None and mission_totals is not None:
            self._tasks.append(
                asyncio.create_task(self._poll_overall(overall_task_id, mission_totals))
            )

        # 等待所有任务完成
        raw_results = await asyncio.gather(*self._tasks, return_exceptions=True)

        # 将异常转换为 MissionResult，跳过 poll task 的 None 返回值
        final: list[MissionResult] = []
        for r in raw_results:
            if isinstance(r, MissionResult):
                final.append(r)
            elif isinstance(r, asyncio.CancelledError):
                final.append(MissionResult.CANCELED)
            elif r is None:
                # _poll_overall 的正常/取消退出均返回 None，不记入结果
                continue
            else:
                final.append(MissionResult.FAILED)

        self.emit("all_finished")
        return final

    async def _run_one(
        self, index: int, mission: Mission, sem: asyncio.Semaphore
    ) -> MissionResult:
        """执行单个 Mission（在 semaphore 保护下）。

        Args:
            index: Mission 在列表中的序号
            mission: 要执行的 Mission
            sem: 并发控制信号量

        Returns:
            MissionResult: 执行结果
        """

        await sem.acquire()
        try:
            # 检查是否已触发全部取消
            if self._cancel_all_event.is_set():
                return MissionResult.CANCELED
            # 创建 executor
            executor = self._executor_factory(mission)

            # 通用中继：将 executor 事件转发为 scheduler 聚合事件。
            # 流式数据事件透传原始参数；其他生命周期事件传 executor.status 快照。
            for evt in _RELAY_EVENTS:
                if evt in (PROGRESS_UPDATED, STATUS_UPDATED, VERBOSE):
                    executor.on(
                        evt,
                        lambda *args, e=evt: self.emit(f"mission_{e}", index, *args),
                    )
                else:
                    executor.on(
                        evt,
                        lambda *args, e=evt, ex=executor: self.emit(
                            f"mission_{e}", index, ex.status
                        ),
                    )

            self._running_count += 1
            self._running_executors[index] = executor
            self.emit("mission_started", index, executor.status)

            # 实时推送：输入文件立即记入 appenv
            for input_spec in mission.inputs:
                appenv.processed_files.append(input_spec.filename)

            result = await executor.execute()

            # 实时推送：garbage 文件立即记入 appenv（崩溃安全）
            appenv.add_garbage_files(*executor.garbage_files)

            # 仅成功完成的任务登记生成文件
            if result == MissionResult.SUCCESS:
                for output_spec in mission.outputs:
                    appenv.generated_files.append(output_spec.filename)

            self._results[index] = result
            self._completed_count += 1
            self.emit("mission_finished", index, executor.status)
            return result

        finally:
            # 在 executor 从 _running_executors 移除前，缓存其 final total_time
            executor = self._running_executors.get(index)
            if executor is not None:
                ci = executor.status.coding_info
                if (
                    ci is not None
                    and ci.total_time is not None
                    and ci.total_time.total_seconds > 0
                ):
                    self._mission_total_cache[index] = ci.total_time.total_seconds
            self._running_executors.pop(index, None)
            self._running_count -= 1
            sem.release()

    async def _poll_overall(
        self, overall_task_id: TaskID, mission_totals: list[float]
    ) -> None:
        """异步轮询所有 executor 的 coding_info，聚合总体进度并刷新进度条。

        退出条件：所有 mission 完成（_completed_count >= total）；
        被 cancel_all() 取消时，poll task 被 CancelledError 终止。
        """
        last_completed = -1.0
        last_total = -1.0
        total_missions = len(self._missions)
        try:
            while True:
                if self._completed_count >= total_missions:
                    # 全部完成：最后一次确保 completed == total == 100%
                    overall_total = sum(mission_totals)
                    appenv.progress.update(
                        overall_task_id, completed=overall_total, total=overall_total
                    )
                    break

                completed = 0.0
                total = 0.0

                for index, mt in enumerate(mission_totals):
                    dur = self._get_duration_for_mission(index, mission_totals)
                    total += dur
                    if index in self._results:
                        # 已完成 → completed 取完整 total
                        completed += dur
                    elif index in self._running_executors:
                        executor = self._running_executors[index]
                        ci = executor.status.coding_info
                        completed += (
                            ci.current_time.total_seconds if ci is not None else 0.0
                        )
                    # 未开始 → completed += 0

                if completed != last_completed or total != last_total:
                    appenv.progress.update(
                        overall_task_id, completed=completed, total=total
                    )
                    last_completed = completed
                    last_total = total

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass

    def _get_duration_for_mission(
        self, index: int, mission_totals: list[float]
    ) -> float:
        """Per-mission 总时长，按 fallback 链获取。所有状态（运行中/已完成/未开始）使用同一逻辑。

        Fallback 优先级：
        1. coding_info.total_time（FFmpeg 运行时报告的 Duration，帧精确）
        2. _mission_total_cache（mission 完成时从 coding_info.total_time 缓存）
        3. mission_totals[index]（预计算值，MediaDB → 1.0）
        4. 1.0（安全兜底）

        优先级 1 和 2 确保同一 task 完成前后 total 值不变，避免进度条跳变。
        MissionPretender 不产生 coding_info，始终走后两项 fallback。
        """
        # 1. 运行中的 executor → 取 coding_info.total_time
        executor = self._running_executors.get(index)
        if executor is not None:
            ci = executor.status.coding_info
            if (
                ci is not None
                and ci.total_time is not None
                and ci.total_time.total_seconds > 0
            ):
                return ci.total_time.total_seconds
        # 2. 已完成的 mission → 取缓存的 total_time
        cached = self._mission_total_cache.get(index)
        if cached is not None and cached > 0:
            return cached
        # 3. Pre-computed mission_totals（MediaDB → 1.0）
        return mission_totals[index] if index < len(mission_totals) else 1.0
