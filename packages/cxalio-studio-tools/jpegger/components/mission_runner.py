from collections.abc import Iterable
from cx_tools.i18n import _
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Condition
from time import sleep

from PIL import Image

from cx_studio.filesystem import ensure_new_file
from cx_tools.app import SafeError
from cx_wealth import WealthLabel
from cx_wealth import rich_types as r
from .errors import NoSourceFileError, TargetingSourceFileError
from .mission import Mission
from ..appenv import appenv


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
            appenv.say(f"[yellow]{_('创建目录')} {parent}[/]")
            parent.mkdir(parents=True, exist_ok=True)

    def run_mission(self, mission: Mission):
        result_tag = "[green]DONE[/]"
        try:

            if not mission.source.exists():
                raise NoSourceFileError(
                    _("源文件 {path} 不存在").format(path=mission.source)
                )

            target = mission.target
            if target.exists():
                if target == mission.source:
                    raise TargetingSourceFileError(
                        _("目标文件 {path} 与源文件相同").format(path=target)
                    )
                if not appenv.context.overwrite:
                    target = ensure_new_file(target)
                    appenv.whisper(
                        f"[yellow]{_('目标文件已存在，已自动重命名为{name}。').format(name=target.name)}[/]"
                    )

            self.check_parent(target)

            img = Image.open(mission.source)
            img = mission.filter_chain.run(img)
            img.save(target, format=mission.target_format, **mission.saving_options)
        except Image.UnidentifiedImageError:
            appenv.say(
                f"[red]{_('文件 {path} 无法识别，任务跳过！').format(path=mission.source)}[/]"
            )
            result_tag = "[red]ERROR[/]"
        except SafeError as e:
            appenv.say(e.message, style=e.style)
            result_tag = "[yellow]SKIPPED[/]"
        except Exception as e:
            appenv.say(
                f"[red]{_('文件 {path} 处理失败！').format(path=mission.source)}[/]"
            )
            appenv.say(e)
            result_tag = "[red]UNKNOWN ERROR[/]"
        finally:
            appenv.say(r.Columns([WealthLabel(mission), result_tag], expand=True))

    def run(self):
        with appenv.console.status(_("正在执行任务...")) as status:
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
                    status.update(_("正在执行{count}个任务...").format(count=remains))
                    sleep(0.05)
