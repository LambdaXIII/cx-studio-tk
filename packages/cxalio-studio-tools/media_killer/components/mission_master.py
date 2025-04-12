from tracemalloc import start
from unittest import runner
from .mission import Mission
from cx_studio.core import CxTime, FileSize
from cx_studio.ffmpeg import FFmpegAsync
import asyncio
from collections.abc import Iterable
from ..appenv import appenv

from dataclasses import dataclass
from collections import defaultdict
import ulid
from .mission_runner import MissionRunner
from media_killer.components import mission
from rich.progress import TaskID


class PoisonError(Exception):
    pass


class MissionMaster:
    @dataclass
    class MInfo:
        mission_id: ulid.ULID
        task_id: TaskID
        # completed:float=0
        total: float | None = None
        # description:str = ""
        runner: MissionRunner | None = None

    def __init__(self, missions: Iterable[Mission], max_workers: int | None = None):
        self._missions = list(missions)
        self._max_workers = max_workers or 1
        self._mission_infos: dict[ulid.ULID, MissionMaster.MInfo] = {}
        self._semaphore = asyncio.Semaphore(self._max_workers)
        self._info_lock = asyncio.Lock()
        self._running_cond = asyncio.Condition()
        self._total_task = appenv.progress.add_task("总进度")
        # self._finished = asyncio.Event()

    async def _build_mission_info(self, mission: Mission):
        async with self._semaphore:
            mission_info = MissionMaster.MInfo(
                mission_id=mission.mission_id,
                task_id=appenv.progress.add_task(
                    mission.name, total=None, visible=False, start=False
                ),
            )
            # mission_info.description = mission.name
            ffmpeg = FFmpegAsync(mission.preset.ffmpeg)
            basic_info = await ffmpeg.get_basic_info(mission.source)
            mission_info.total = (
                basic_info["duration"].total_seconds
                if "duraiton" in basic_info
                else None
            )

            async with self._info_lock:
                self._mission_infos[mission.mission_id] = mission_info

            if appenv.context.pretending_mode:
                await asyncio.sleep(0.5)

    async def _run_mission(self, mission: Mission):
        if appenv.wanna_quit:
            return
        async with self._semaphore:
            runner = MissionRunner(mission)
            async with self._info_lock:
                self._mission_infos[mission.mission_id].runner = runner
            t = asyncio.create_task(runner.execute())
            appenv.progress.start_task(self._mission_infos[mission.mission_id].task_id)
            while not t.done():
                if appenv.wanna_quit:
                    runner.cancel()
                    break
                await asyncio.sleep(0.1)
            await t
            appenv.progress.stop_task(self._mission_infos[mission.mission_id].task_id)

    async def _scan_tasks(self) -> tuple[float, float, float, float]:
        t_total = t_completed = t_current = 0
        total_count = done_count = 0

        for info in self._mission_infos.values():
            total_count += 1
            t_total += info.total or 1
            if not info.runner:
                continue
            if info.runner.is_running():
                appenv.progress.update(
                    info.task_id,
                    visible=True,
                    # start=True,
                    description=info.runner.task_description,
                    completed=info.runner.task_completed,
                    total=info.runner.task_total,
                )
                # appenv.say(info.runner.task_total)
                if info.total is None:
                    info.total = info.runner.task_total
                t_current += info.runner.task_completed
            else:
                appenv.progress.update(info.task_id, visible=False, start=False)
                if info.runner.done():
                    done_count += 1
                    t_completed += info.runner.task_completed
        return t_completed + t_current, t_total, done_count, total_count

    @staticmethod
    async def _poison_task():
        raise PoisonError()

    async def run(
        self,
    ):
        try:
            async with self._running_cond:
                appenv.progress.update(
                    self._total_task, start=True, visible=True, total=len(self._missions)
                )
                for mission in appenv.progress.track(
                    self._missions, task_id=self._total_task
                ):
                    appenv.progress.update(self._total_task, description=mission.name)
                    await self._build_mission_info(mission)

                async with asyncio.TaskGroup() as task_group:
                    workers = [
                        task_group.create_task(self._run_mission(x)) for x in self._missions
                    ]

                    while not all(x.done() for x in workers):
                        if appenv.really_wanna_quit:
                            task_group.create_task(self._poison_task())
                            break
                        t_completed, t_total, t_count, d_count = await self._scan_tasks()
                        appenv.progress.update(
                            self._total_task,
                            completed=t_completed,
                            total=t_total,
                            description="总体进度",
                        )
                        if t_count == d_count:
                            break
                        await asyncio.sleep(0.1)
                    # while checking

                    await asyncio.wait(workers)
                # taskgroup
            # running Condition
        except *PoisonError:
            appenv.say("所剩余任务被取消")

