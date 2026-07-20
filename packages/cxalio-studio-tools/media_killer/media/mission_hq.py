"""MissionHQ — 异步任务执行底座，media_killer 的顶层入口。

MissionHQ 是唯一对外暴露的顶层组件，统一管理 Mission 执行的完整生命周期：
任务投喂 → 并发调度 → 进度显示 → 中断响应 → 事件总线。

组件架构：
    MissionHQ (事件总线 + 生命周期)
    ├── ExecutorFactory  (装配 executor/pretender)
    ├── ExecutorScheduler (并发控制 + 中断)
    ├── TaskProgress      (子进度条，事件驱动)
    ├── TotalProgress     (总进度条，2Hz 轮询)
    └── Whisperer         (debug 消息转发，通过 Factory 装配)

事件总线（HQ 级）：
    - mission_started  — (mission) 单个 mission 开始执行
    - mission_result   — (mission, result) 单个 mission 执行完成
    - file_logged      — (FileLogType, list[str]) 文件处理事件
    - finished         — () 全部 mission 执行完成

中断语义（两段式）：
    - cancel()：取消正在执行的 executor，待办队列不受影响
    - abort()：取消全部 executor + 清空待办队列
    两者均能唤醒 paused 状态（通过 _resume_event.set()）
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pyee.asyncio import AsyncIOEventEmitter

from .executor import FfmpegErrorInfo, MissionResult
from .executor_factory import ExecutorFactory
from .executor_scheduler import ExecutorScheduler
from cx_studio.tui.tools.double_trigger import FIRST_TRIGGERED, SECOND_TRIGGERED
from cx_wealthy import WealthyDetailPanel
from .mission import Mission
from .task_progress import TaskProgress
from .total_progress import TotalProgress

if TYPE_CHECKING:
    from rich.progress import Progress

    from cx_tools.app import IAppEnvironment

# ── HQ 级事件名常量 ─────────────────────────────────────────

MISSION_STARTED: str = "mission_started"
MISSION_RESULT: str = "mission_result"
MISSION_FILE_LOGGED: str = "file_logged"
MISSION_FINISHED: str = "finished"


@dataclass
class ProgressSnapshot:
    """总进度瞬时快照。

    每次轮询由 progress_snapshot() 计算一次，避免在轮询间隔内
    遍历 _all_missions 时因并发修改导致数据不一致。

    Attributes:
        total: 全部任务预估总时长（秒）
        completed: 已完成任务的累积时长（秒）
    """

    total: float
    completed: float


class MissionHQ(AsyncIOEventEmitter):
    """异步任务执行底座。

    唯一对外暴露的顶层组件，封装 Mission 执行的全部生命周期。
    继承 AsyncIOEventEmitter 提供事件总线——Application 通过 on() 订阅
    mission_started / mission_result / file_logged / finished 事件。

    并发模型：
        使用 create_task + gather 模式，而非设计文档中的顺序 await。
        ExecutorScheduler.run_one 内部通过 asyncio.Semaphore 控制
        max_workers 并发度——这使得 max_workers 配置真正生效，
        同时保留 queue 模型的动态投喂能力。

    Attributes:
        _max_workers: 最大并发 worker 数（≥1）
        _pretending: Pretend 模式标志
        _queue: 待执行 Mission 队列
        _all_missions: 全部已入队 Mission 列表（用于索引和快照）
        _mission_executor: Mission → executor_id 映射
        _finished: 投喂完成标志（CLI 模式在 run() 前设置）
        _paused: 暂停标志
        _resume_event: 暂停恢复事件
        _interrupt_event: 全局中断事件
        _completed_duration_cache: 已完成任务 duration 缓存（防跳变）
        _ABORT_SENTINEL: 中止哨兵，用 is 比较唤醒 run() 循环
    """

    def __init__(
        self,
        max_workers: int = 1,
        pretending: bool = False,
        progress: "Progress | None" = None,
        env: "IAppEnvironment | None" = None,
        scheduler: "ExecutorScheduler | None" = None,
        factory: "ExecutorFactory | None" = None,
    ) -> None:
        """初始化 MissionHQ。

        Args:
            max_workers: 最大并发 worker 数，默认 1
            pretending: 是否启用 Pretend 模式（-p/--pretend）
            progress: Rich Progress 实例，None 则禁用进度显示
            env: IAppEnvironment 实例，用于中断接入和 Whisperer
            scheduler: 自定义 ExecutorScheduler（测试注入用）
            factory: 自定义 ExecutorFactory（测试注入用）
        """
        super().__init__()
        self._max_workers = max(1, max_workers)
        self._pretending = pretending
        self._queue: asyncio.Queue[Mission] = asyncio.Queue()
        self._all_missions: list[Mission] = []
        self._mission_executor: dict[Mission, int] = {}
        self._finished = False
        self._paused = False
        self._resume_event = asyncio.Event()
        self._resume_event.set()  # 初始非暂停状态
        self._interrupt_event = asyncio.Event()
        self._results: list[MissionResult] = []
        # 已完成任务的 duration 缓存，防止进度条跳变
        # key = executor_id, value = 运行时 coding_info.total_time（秒）
        self._completed_duration_cache: dict[int, float] = {}
        # 中止哨兵：用 is 比较，不依赖 Mission.__eq__
        self._ABORT_SENTINEL = Mission(
            ffmpeg="abort",
            source=Path("<abort>"),
            standard_target=Path("<abort>"),
            overwrite=False,
            options=(),
            inputs=[],
            outputs=[],
        )
        # 子组件（默认自动创建，可注入用于测试）
        self._factory = factory or ExecutorFactory(self)
        self._scheduler = scheduler or ExecutorScheduler(self)
        self._task_progress = TaskProgress(self) if progress else None
        self._total_progress = TotalProgress(self) if progress else None
        # 中断接入：将 first_triggered → cancel, second_triggered → abort
        if env is not None:

            @env.interrupt_handler.on(FIRST_TRIGGERED)
            def _cancel() -> None:
                self.cancel()

            @env.interrupt_handler.on(SECOND_TRIGGERED)
            def _abort() -> None:
                self.abort()

        self._env = env
        self._progress = progress

    # ── 任务投喂 ──────────────────────────────────────────────

    def add_missions(self, missions: list[Mission]) -> None:
        """同步入队并记入全量列表。

        可在任何上下文调用（同步）。Mission 入队后即可被 run() 消费。

        Args:
            missions: 待执行的 Mission 列表
        """
        for m in missions:
            self._queue.put_nowait(m)
            self._all_missions.append(m)

    def finish(self) -> None:
        """标记不再投喂新任务。

        CLI 模式在 run() 前调用。run() 检测到 _finished 且队列为空时退出循环。
        Server 模式不调用此方法——run() 持续等待新任务。
        """
        self._finished = True

    # ── 运行 ──────────────────────────────────────────────────

    async def run(self) -> list[MissionResult]:
        """主循环：消费队列 → 创建 executor → 调度执行。

        并发模型（与设计文档 02-components.md 的区别）：
        循环中为每个 mission 创建 asyncio.Task，而非顺序 await。
        ExecutorScheduler.run_one 内部用 semaphore 控制并发度。
        循环结束后 gather 所有 task 收集结果。
        这让 max_workers 配置真正生效，同时保留 queue 的动态投喂能力。

        返回前必须等待所有已启动的 task 完成（包括取消的），
        否则 garbage_files 可能未完整收集。

        Returns:
            list[MissionResult]: 每个 Mission 的执行结果列表
        """
        total_task = None
        if self._total_progress:
            total_task = asyncio.create_task(self._total_progress.run())

        pending_tasks: list[asyncio.Task] = []

        try:
            while not (self._finished and self._queue.empty()):
                # 暂停检查
                if self._paused:
                    await self._resume_event.wait()

                # 中断检查
                if self._interrupt_event.is_set():
                    break

                mission = await self._queue.get()
                # 中止哨兵：abort() 放入此对象，唤醒被 get() 阻塞的循环
                if mission is self._ABORT_SENTINEL:
                    break

                task = asyncio.create_task(self._run_one(mission))
                pending_tasks.append(task)

            # 等待所有已启动的 task 完成
            raw_results = await asyncio.gather(*pending_tasks, return_exceptions=True)
            for r in raw_results:
                if isinstance(r, MissionResult):
                    self._results.append(r)
                elif isinstance(r, asyncio.CancelledError):
                    self._results.append(MissionResult.CANCELED)
                elif r is not None:
                    self._results.append(MissionResult.FAILED)

            self.emit(MISSION_FINISHED)
        finally:
            if total_task is not None:
                total_task.cancel()
                try:
                    await total_task
                except asyncio.CancelledError:
                    pass

        return self._results

    # ── 中断 ──────────────────────────────────────────────────

    def cancel(self) -> None:
        """取消正在执行的 executor，待办队列不受影响。

        只取消当前通过 semaphore 正在运行的任务。
        semaphore 上等待的任务不受影响——acquire 后正常执行。
        这与旧版 MissionScheduler.cancel_running() 行为一致。

        要取消全部任务（含等待中的），调用 abort()。
        """
        self._scheduler.cancel_running()
        self._resume_event.set()  # 确保 pause 状态也被唤醒

    def abort(self) -> None:
        """取消全部 executor + 清空待办队列。

        1. ExecutorScheduler.cancel_all() → 取消所有 running executor
           + 设置 _abort_event（后续 semaphore 获取后立即返回 CANCELED）
        2. 清空待办队列（_queue.get_nowait 直到 QueueEmpty）
        3. 设置全局中断标志（_interrupt_event）
        4. 放入中止哨兵（唤醒被 queue.get() 阻塞的 run() 循环）
        5. 唤醒 paused 状态
        """
        self._scheduler.cancel_all()
        # 清空待办队列
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._interrupt_event.set()
        self._resume_event.set()  # 确保 pause 状态也被唤醒
        # 放入中止哨兵，唤醒被 queue.get() 阻塞的 run() 循环
        self._queue.put_nowait(self._ABORT_SENTINEL)

    # ── 暂停控制 ──────────────────────────────────────────────

    @property
    def paused(self) -> bool:
        """是否处于暂停状态。

        Returns:
            bool: True 表示暂停中，run() 循环阻塞在 _resume_event.wait()
        """
        return self._paused

    @paused.setter
    def paused(self, value: bool) -> None:
        """设置暂停状态。

        Args:
            value: True = 暂停（clear _resume_event），False = 恢复（set _resume_event）
        """
        self._paused = value
        if not value:
            self._resume_event.set()
        else:
            self._resume_event.clear()

    # ── 关闭 ──────────────────────────────────────────────────

    def shutdown(self) -> None:
        """终止全部执行。Server 模式调用。

        组合调用 finish() + abort()：
        finish() 标记不再投喂 → abort() 取消全部执行并唤醒 run() 退出。
        """
        self.finish()
        self.abort()

    async def _run_one(self, mission: Mission) -> MissionResult:
        """执行单个 Mission 的完整生命周期。

        流程：
        1. 检查中止状态——如已 abort，直接返回 CANCELED，不创建 executor
        2. 通过 Factory 创建 executor
        3. 传入 on_start callback 给 run_one（在 semaphore 获取后执行）
           - 记录 mission → executor_id 映射
           - emit mission_started
           - 创建子进度条
        4. run_one 管理 semaphore 和中断检查，然后执行 executor
        5. 缓存完成时长（防进度条跳变）
        6. emit mission_result
        7. finally 中清理子进度条（确保异常安全）

        Args:
            mission: 待执行的 Mission

        Returns:
            MissionResult: 执行结果
        """
        # 提前检查中止——避免 abort 后 pending_tasks 仍创建 executor 对象
        if self._scheduler.is_aborted:
            return MissionResult.CANCELED
        executor = self._factory(mission)
        index = self._all_missions.index(mission)

        def _on_start() -> None:
            """在 run_one 获取 semaphore 并通过中断检查后执行。"""
            self._mission_executor[mission] = executor.executor_id
            self.emit(MISSION_STARTED, mission)
            if self._task_progress:
                self._task_progress.watch(executor, index)

        try:
            result = await self._scheduler.run_one(executor, on_start=_on_start)
            # 缓存已完成任务的 duration，防止进度条跳变
            self._cache_completed_duration(executor)
            if result == MissionResult.FAILED and self._env is not None:
                error_info = executor.make_error_info()
                self._env.whisper(
                    WealthyDetailPanel(
                        error_info,
                        title="[cx.error]FFmpeg 异常退出[/]",
                    )
                )
            self.emit(MISSION_RESULT, mission, result)
            return result
        finally:
            if self._task_progress:
                self._task_progress.forget(executor)

    def _cache_completed_duration(self, executor) -> None:
        """从 executor 的 coding_info 缓存 total_time 到 _completed_duration_cache。

        用于 _duration_for() 的 fallback 链——已完成任务的 coding_info
        可能在 executor GC 后不可达，缓存确保进度条不会因数据丢失而跳变。

        Args:
            executor: 已完成执行的 MissionExecutor 实例
        """
        ci = executor.status.coding_info
        if (
            ci is not None
            and ci.total_time is not None
            and ci.total_time.total_seconds > 0
        ):
            self._completed_duration_cache[executor.executor_id] = (
                ci.total_time.total_seconds
            )

    def progress_snapshot(self) -> ProgressSnapshot:
        """全量任务进度快照。

        每轮轮询调用一次（TotalProgress._sync）。
        先获取调度器状态快照（冻住 running/completed 集合），
        再遍历 _all_missions 从快照计算累计值，
        避免在遍历过程中因 executor 状态变化导致数据不一致。

        返回值中 completed 被 clamp 到 [0, total] 区间，
        确保富进度条不出现负值或 >100%。

        Returns:
            ProgressSnapshot: total 和 completed 的瞬时快照
        """
        total = 0.0
        completed = 0.0
        snap = self._scheduler.snapshot()
        for mission in self._all_missions:
            dur = self._duration_for(mission, snap)
            total += dur
            eid = self._mission_executor.get(mission)
            if eid is not None and eid in snap.completed:
                completed += dur
            elif eid is not None and eid in snap.running:
                executor = snap.running[eid]
                ci = executor.status.coding_info
                if ci is not None:
                    completed += ci.current_time.total_seconds
        return ProgressSnapshot(
            total=max(total, 0.0),
            completed=min(max(completed, 0.0), max(total, 0.0)),
        )

    def _duration_for(
        self, mission: Mission, snap: "ExecutorScheduler.SchedulerSnapshot"
    ) -> float:
        """Per-mission 预估时长，带 fallback 链。

        优先级（从高到低）：
        1. 正在运行的 executor → coding_info.total_time（帧精确，实时变化）
        2. 已完成任务的缓存 → _completed_duration_cache（完成时冻住的快照）
        3. 1.0 秒兜底（未开始的任务默认时长）

        第 2 级是防跳变的关键——如果对已完成任务继续使用
        coding_info.total_time，可能在 executor GC 后回退到 1.0，
        导致进度条从接近完成跳回一半。

        Args:
            mission: 当前遍历的 Mission
            snap: SchedulerSnapshot 冻住快照

        Returns:
            float: 该 mission 的预估总时长（秒），≥ 0
        """
        eid = self._mission_executor.get(mission)
        if eid is not None:
            # 优先级 1：运行中 → 帧精确实时值
            running = snap.running.get(eid)
            if running is not None:
                ci = running.status.coding_info
                if (
                    ci is not None
                    and ci.total_time is not None
                    and ci.total_time.total_seconds > 0
                ):
                    return ci.total_time.total_seconds
            # 优先级 2：已完成 → 冻住的缓存值
            cached = self._completed_duration_cache.get(eid)
            if cached is not None and cached > 0:
                return cached
        # 优先级 3：兜底
        return 1.0
