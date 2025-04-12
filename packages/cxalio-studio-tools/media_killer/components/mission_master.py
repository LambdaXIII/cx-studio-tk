import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from rich.progress import TaskID

from cx_studio.ffmpeg import FFmpegAsync
from cx_studio.utils.tools import AsyncCanceller
from cx_studio.utils.tools.job_counter import JobCounter
from .mission import Mission
from .mission_runner import MissionRunner
from ..appenv import appenv


class PoisonError(Exception):
    pass


class MissionMaster:
    @dataclass
    class MInfo:
        mission: Mission
        task_id: TaskID
        total: float | None = None
        runner: MissionRunner | None = None

    def __init__(self, missions: Iterable[Mission], max_workers: int | None = None):
        self._missions = list(missions)
        self._max_workers = max_workers or 1
        self._mission_infos: dict[int, MissionMaster.MInfo] = {}
        self._semaphore = asyncio.Semaphore(self._max_workers)
        self._info_lock = asyncio.Lock()
        self._running_cond = asyncio.Condition()
        self._total_task = appenv.progress.add_task("总进度")

        self._cancel_one = AsyncCanceller()
        self._cancel_all_event = asyncio.Event()

    async def _build_mission_info(self, index):
        mission = self._missions[index]
        ffmpeg = FFmpegAsync(mission.preset.ffmpeg)
        basic_info = await ffmpeg.get_basic_info(mission.source)
        duration = basic_info.get("duration")
        mission_info = MissionMaster.MInfo(
            mission=mission,
            task_id=appenv.progress.add_task(
                mission.name, total=None, visible=False, start=False
            ),
            total=duration.total_seconds if duration else None,
        )

        async with self._info_lock:
            self._mission_infos[index + 1] = mission_info

        if appenv.context.pretending_mode:
            await asyncio.sleep(0.2)

    async def _run_mission(self, index: int):
        async with self._semaphore:
            if self._cancel_all_event.is_set():
                return

            mission_info = self._mission_infos[index]
            mission = mission_info.mission
            runner = MissionRunner(mission)

            async with self._info_lock:
                self._mission_infos[index].runner = runner

            t = asyncio.create_task(runner.execute())

            appenv.progress.start_task(mission_info.task_id)
            try:
                while not t.done():
                    wanna_quit = await self._cancel_one.is_cancelling_async()
                    if wanna_quit or self._cancel_all_event.is_set():
                        runner.cancel()
                        break
                    await asyncio.sleep(0.1)

                # await t

            except asyncio.CancelledError:
                runner.cancel()
                # raise
            finally:
                appenv.progress.stop_task(mission_info.task_id)
                if appenv.context.pretending_mode:
                    await asyncio.sleep(1)

    async def _update_tasks(self):
        mission_count = len(self._missions)
        total_time = completed_time = 0
        start_time = datetime.now()

        async with self._info_lock:
            infos = self._mission_infos.copy()

        jobs = JobCounter(mission_count)

        for index, info in infos.items():
            jobs.current = index
            total_time += info.total or 1

            if not info.runner:
                continue

            runner_start_time = info.runner.task_start_time
            if runner_start_time is not None and runner_start_time < start_time:
                start_time = runner_start_time

            if info.runner.is_running():
                desc_str = "[bright_black][{}] [{:.2f}x][/] [yellow]{}[/]".format(
                    jobs.format(), info.runner.task_speed, info.runner.task_description
                )

                appenv.progress.update(
                    info.task_id,
                    visible=True,
                    description=desc_str,
                    completed=info.runner.task_completed,
                    total=info.runner.task_total,
                )

                completed_time += info.runner.task_completed
            else:
                appenv.progress.update(info.task_id, visible=False)
                if info.runner.done():
                    completed_time += info.runner.task_total or 1
        # for
        speed = completed_time / (datetime.now() - start_time).total_seconds()
        desc_str = "[bright_black][{:.2f}x][/] [blue]总体进度[/]".format(speed)

        appenv.progress.update(
            self._total_task,
            completed=completed_time,
            total=total_time,
            description=desc_str,
        )

    # async def _scan_tasks(self) -> tuple[float, float, float, float]:
    #     t_total = t_completed = t_current = 0
    #     done_count = 0
    #     total_start_time = datetime.now()

    #     async with self._info_lock:
    #         infos = self._mission_infos.copy()

    #     infos_length = len(infos)
    #     jobs = JobCounter(infos_length, start=0)
    #     for index, info in infos.items():
    #         jobs.current = index

    #         t_total += info.total or 1

    #         if not info.runner:
    #             continue

    #         runner_start = info.runner.task_start_time
    #         if runner_start is not None and runner_start < total_start_time:
    #             total_start_time = runner_start

    #         if info.runner.is_running():
    #             desc_str = "[bright_black][{}] [{:.2f}x][/] [yellow]{}[/]".format(
    #                 jobs.format(), info.runner.task_speed, info.runner.task_description
    #             )

    #             appenv.progress.update(
    #                 info.task_id,
    #                 visible=True,
    #                 description=desc_str,
    #                 completed=info.runner.task_completed,
    #                 total=info.runner.task_total,
    #             )

    #             if info.total is None:
    #                 info.total = info.runner.task_total

    #             t_current += info.runner.task_completed
    #         else:
    #             appenv.progress.update(info.task_id, visible=False)
    #             if info.runner.done():
    #                 done_count += 1
    #                 t_completed += info.runner.task_completed

    #     speed = (
    #         t_completed
    #         / (datetime.now() - total_start_time).total_seconds()
    #     )
    #     desc_str = (
    #         "[bright_black][{:.2f}x][/] [blue]总体进度[/]".format(
    #             speed
    #         )
    #     )

    #     appenv.progress.update(
    #         self._total_task,
    #         completed=t_completed,
    #         total=t_total,
    #         description=desc_str,
    #     )
    #     return t_completed + t_current, t_total, done_count, infos_length

    @staticmethod
    async def _poison_task():
        raise PoisonError()

    async def run(self):
        try:
            self._cancel_all_event.clear()
            total_start_time = datetime.now()
            async with self._running_cond:
                appenv.progress.update(
                    self._total_task,
                    start=True,
                    visible=True,
                    total=len(self._missions),
                )

                for index, mission in appenv.progress.track(
                    enumerate(self._missions), task_id=self._total_task
                ):
                    appenv.progress.update(self._total_task, description=mission.name)
                    await self._build_mission_info(index)

                workers = [
                    asyncio.create_task(self._run_mission(x))
                    for x in self._mission_infos
                ]

                while not all(x.done() for x in workers):
                    if appenv.wanna_quit_event.is_set():
                        self._cancel_one.cancel()
                        appenv.wanna_quit_event.clear()

                    if appenv.really_wanna_quit_event.is_set():
                        self._cancel_all_event.set()
                        for t in workers:
                            t.cancel()
                        done, pending = await asyncio.wait(
                            workers, return_when=asyncio.ALL_COMPLETED
                        )
                        for p in pending:
                            p.cancel()
                        await asyncio.sleep(1)
                        break

                    await self._update_tasks()
                    await asyncio.sleep(0.1)
                # while checking

                asyncio.gather(*workers, return_exceptions=True)

                # taskgroup
            # running Condition
        except* PoisonError:
            appenv.say("剩余任务被取消")
