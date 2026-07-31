"""纯调度算法模块。

管理并发控制（semaphore）、执行 executor、响应中断。
不涉及进度显示、事件总线或 UI 适配——那些是 MissionHQ 的职责。

与旧版 components/scheduler.py 的关键对齐：
- cancel_all 幂等（scheduler.py:185-186）
- semaphore 获取后中断检查（scheduler.py:256-258）
- 异常由 MissionHQ._run_one 统一捕获并报告
"""

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .executor import MissionExecutor, MissionResult

if TYPE_CHECKING:
    from .mission_hq import MissionHQ


class ExecutorScheduler:
    """纯调度算法。管理并发执行、中断信号和运行状态快照。

    职责：
    - 通过 asyncio.Semaphore 控制 max_workers 并发度
    - 维护 running/completed 集合，提供 snapshot 给 progress_snapshot 使用
    - 通过 _abort_event 实现两段式中断：cancel_running（取消运行中）和 cancel_all（取消全部）

    Attributes:
        _hq: 反向引用 MissionHQ
        _sem: 并发度控制信号量，值 = max_workers
        _running: 当前正在执行的 executor_id → executor 映射
        _completed: 已完成执行的 executor_id 集合
        _abort_event: 全局中断事件，set 后所有排队任务直接返回 CANCELED
    """

    def __init__(self, hq: "MissionHQ"):
        """初始化调度器。

        Args:
            hq: MissionHQ 实例引用，从中读取 max_workers 配置
        """
        self._hq = hq
        self._sem = asyncio.Semaphore(hq._max_workers)
        self._running: dict[int, MissionExecutor] = {}
        self._completed: set[int] = set()
        self._abort_event = asyncio.Event()

    @property
    def is_aborted(self) -> bool:
        """是否已中止（_abort_event 已设置）。

        MissionHQ._run_one 在创建 executor 前检查此属性，
        避免 abort 后所有 pending task 仍然创建 executor 对象。
        """
        return self._abort_event.is_set()

    async def run_one(self, executor: MissionExecutor, on_start=None) -> MissionResult:
        """异步执行单个 executor，内部管理 semaphore 和中断检查。

        执行流程：
        1. 获取 semaphore（阻塞直到有空位）
        2. 检查 _abort_event（abort 后排队任务直接返回 CANCELED）
        3. **执行 on_start callback**（告知 HQ：执行即将开始，可安全创建 UI）
        4. 注册到 running 集合
        5. 调用 executor.execute()
        6. 完成后移入 completed 集合

        on_start 在 semaphore 获取成功后执行，确保 setup 代码（事件发射、
        进度条创建等）只在真正开始执行时运行，而不是在 create_task
        阶段就全部触发。这解决了 359 个任务一次性创建进度条的问题。

        Args:
            executor: 已装配的 MissionExecutor 实例
            on_start: 可选回调，在获取 semaphore 并通过中断检查后调用。
                      用于"执行开始"时刻的 UI 设置，如发射 mission_started、
                      创建子进度条。scheduler 不关心回调内容，仅提供时序挂钩。

        Returns:
            MissionResult: 执行结果。成功/取消返回 MissionResult；其他异常向上传播至 MissionHQ._run_one
        """
        async with self._sem:
            # 获取 semaphore 后检查中断——abort 后仍在排队的 task 直接返回
            if self._abort_event.is_set():
                return MissionResult.CANCELED

            if on_start is not None:
                on_start()

            eid = executor.executor_id
            self._running[eid] = executor
            try:
                result = await executor.execute()
                self._completed.add(eid)
                return result
            except asyncio.CancelledError:
                return MissionResult.CANCELED
            finally:
                self._running.pop(eid, None)

    def cancel_running(self) -> None:
        """取消所有正在执行的 executor（不清理待办队列）。

        调用每个 running executor 的 cancel() 方法。
        executor 内部会在下一次轮询中检测 _cancel_event 并退出。
        """
        for executor in list(self._running.values()):
            executor.cancel()

    def cancel_all(self) -> None:
        """取消全部 executor 并设置中断标志。

        幂等设计：重复调用为 no-op。
        1. 设置 _abort_event（后续 semaphore 获取后立刻返回 CANCELED）
        2. 取消所有正在运行的 executor
        """
        if self._abort_event.is_set():
            return
        self._abort_event.set()
        self.cancel_running()

    @dataclass
    class SchedulerSnapshot:
        """调度器运行状态的不可变快照。

        Attributes:
            running: 当前运行的 executor_id → executor 映射（副本）
            completed: 已完成的 executor_id 集合（副本）
        """

        running: dict[int, MissionExecutor]
        completed: set[int]

    def snapshot(self) -> "ExecutorScheduler.SchedulerSnapshot":
        """获取当前运行状态快照。

        返回副本以确保线程安全——调用方可以安全地遍历和读取快照
        而不受运行时状态变化的影响。

        Returns:
            SchedulerSnapshot: 运行状态快照
        """
        return ExecutorScheduler.SchedulerSnapshot(
            running=dict(self._running),
            completed=set(self._completed),
        )
