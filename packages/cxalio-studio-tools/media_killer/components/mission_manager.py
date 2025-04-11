import itertools
from cx_tools_common.rich_gadgets import RichLabel
from .mission import Mission
from cx_studio.ffmpeg import FFmpegCodingInfo, FFmpeg
from concurrent import futures
from collections.abc import Iterable
from .mission_runner import MissionRunner
from cx_tools_common.rich_gadgets import MultiProgressManager
from ..appenv import appenv
from cx_studio.core import CxTime
from rich.columns import Columns
from datetime import datetime
from rich.text import Text
import time

class MissionManager:
    def __init__(self, missions:Iterable[Mission],max_workers:int|None=None):
        self._max_workers = max_workers
        self._missions = list(missions)
        # self._futures:list[futures.Future] = []
        # self._runners:list[MissionRunner] = []
        self._progress_manager = MultiProgressManager()


    def work(self,mission:Mission):
        with FFmpeg(mission.preset.ffmpeg, mission.iter_arguments()) as ffmpeg:
            @ffmpeg.on("started")
            def on_started():
                self._progress_manager.show(mission)
                appenv.whisper(f"Started {mission.name}")
                self._progress_manager.update_task(mission,start_time=datetime.now())

            @ffmpeg.on("completed")
            def on_completed():
                end_time = datetime.now()
                self._progress_manager.update_task(mission,end_time=end_time)
                start_time = self._progress_manager.get(mission)[1].start_time
                if start_time:
                    time_span = end_time - start_time
                    time_span_str = CxTime.from_seconds(time_span.total_seconds()).pretty_string
                    appenv.whisper(f"Completed mission {mission.name} took {time_span_str}")
                else:
                    appenv.whisper(f"Completed {mission.name}")
                appenv.say(Columns([RichLabel(mission),Text("完成",style="green",justify="right")]))

            @ffmpeg.on("canceled")
            def on_canceled():
                self._progress_manager.update_task(mission,end_time=datetime.now(),visible=False,canceled=True)
                appenv.whisper(f"Canceled {mission.name}")
                appenv.say(Columns([RichLabel(mission),Text("取消",style="red",justify="right")]))

            @ffmpeg.on("progress_updated")
            def on_progress_updated(current:CxTime,total:CxTime):
                c = current.total_seconds
                t = total.total_seconds if total else None
                self._progress_manager.update_task(mission,completed=c,total=t)

            return ffmpeg.execute()
        # exit

    def execute(self):
        total_task = appenv.progress.add_task("总进度",total=len(self._missions))
        with futures.ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            workers = []
            for m in self._missions:
                self._progress_manager.add_task(m, appenv.progress.add_task(m.name))
                worker = pool.submit(self.work,m)
                workers.append(worker)

            while True:
                if appenv.really_wanna_quit:
                    for worker in workers:
                        worker.cancel()
                    break

                for task_key in self._progress_manager.keys():
                    task_id,status = self._progress_manager.get(task_key)
                    if task_id:
                        appenv.progress.update(task_id,description=status.description,total=status.total,completed=status.completed)
                
                c,t = self._progress_manager.get_total_progress()
                appenv.say(c,t)
                appenv.progress.update(total_task,completed=c,total=t)

                if all(worker.done() for worker in workers):
                    break

                time.sleep(0.1)




            



    