from ast import expr_context
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
from cx_wealth import rich_types as r
from cx_wealth import WealthLabel

from cx_tools.app import SafeError
from .errors import NoSourceFileError, TargetingSourceFileError


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
            appenv.say(f"[yellow]创建目录 {parent}[/]")
            parent.mkdir(parents=True, exist_ok=True)

    def run_mission(self, mission: Mission):
        result_tag = "[green]DONE[/]"
        try:

            if not mission.source.exists():
                raise NoSourceFileError(f"源文件 {mission.source} 不存在")

            target = mission.target
            if target.exists():
                if target == mission.source:
                    raise TargetingSourceFileError(f"目标文件 {target} 与源文件相同")
                if not appenv.context.overwrite:
                    target = PathUtils.ensure_new_file(target)
                    appenv.whisper(
                        f"[yellow]目标文件已存在，已自动重命名为{target.name}。[/]"
                    )

            self.check_parent(target)

            img = Image.open(mission.source)
            img = mission.filter_chain.run(img)
            img.save(target, format=mission.target_format, **mission.saving_options)
        except Image.UnidentifiedImageError:
            appenv.say(f"[red]文件 {mission.source} 无法识别，任务跳过！[/]")
            result_tag = "[red]ERROR[/]"
        except SafeError as e:
            appenv.say(e.message, style=e.style)
            result_tag = "[yellow]SKIPPED[/]"
        except Exception as e:
            appenv.say(f"[red]文件 {mission.source} 处理失败！[/]")
            appenv.say(e)
            result_tag = "[red]UNKOWN ERROR[/]"
        finally:
            appenv.say(r.Columns([WealthLabel(mission), result_tag], expand=True))

    def run(self):
        with appenv.console.status("正在执行任务...") as status:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                tasks = {
                    m.mission_id: executor.submit(self.run_mission, m)
                    for m in self.missions
                }
                while True:
                    done = [task for task in tasks.values() if task.done()]
                    remains = len(tasks) - len(done)
                    if remains == 0:
                        break
                    status.update(f"正在执行{remains}个任务...")
                    sleep(0.05)
