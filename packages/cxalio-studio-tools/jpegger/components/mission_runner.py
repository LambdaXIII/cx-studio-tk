from time import sleep
from .mission import Mission
from PIL import Image

from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from threading import Condition
import ulid
from ..appenv import appenv

from cx_studio.utils import PathUtils
from pathlib import Path


class MissionRunner:
    def __init__(self, missions: Iterable[Mission], max_workers: int = 10):
        self.missions = list(missions)
        self.max_workers = max_workers
        self.dir_condition = Condition()

    def check_parent(self, target: Path):
        parent = target.parent
        if parent.exists():
            return
        with self.dir_condition:
            if parent.exists():
                return
            appenv.say(f"[yellow]正在创建目录 {parent}...[/]")
            parent.mkdir(parents=True, exist_ok=True)

    def run_mission(self, mission: Mission):
        if not mission.source.exists():
            appenv.say(f"[red]文件 {mission.source} 不存在，任务跳过！[/]")
            return

        target = mission.target
        if target.exists():
            if target == mission.source:
                appenv.say(f"[red]目标文件 {target} 与源文件相同，任务跳过！[/]")
                return
            if not appenv.context.overwrite:
                target = PathUtils.ensure_new_file(target)
                appenv.say(f"[yellow]目标文件已存在，已自动重命名为{target.name}。[/]")

        self.check_parent(target)

        img = Image.open(mission.source)
        img = mission.filter_chain.run(img)
        img.save(target, format=mission.target_format)
        appenv.say(
            f"[green]DONE[/] [yellow]{mission.source.name}[/] -> [yellow]{target}[/]"
        )

    def run(self):
        with appenv.console.status("正在执行任务...") as status:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                tasks = {m: executor.submit(self.run_mission, m) for m in self.missions}
                while True:
                    done = [task for task in tasks.values() if task.done()]
                    remains = len(tasks) - len(done)
                    if remains == 0:
                        break
                    status.update(f"正在执行{remains}个任务...")
                    sleep(0.05)
