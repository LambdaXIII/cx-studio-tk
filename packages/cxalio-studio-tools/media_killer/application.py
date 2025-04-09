import asyncio
import importlib.resources
import importlib.resources
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import override

from cx_studio.utils import PathUtils
from cx_tools_common.app_interface import IApplication
from cx_tools_common.exception import SafeError
from cx_tools_common.rich_gadgets import DynamicColumns
from cx_tools_common.rich_gadgets import (
    IndexedListPanel,
)
from cx_tools_common.rich_gadgets import RichDetailPanel
from .components.mission_runner import MissionRunner
from .appenv import appenv
from .components import (
    InputScanner,
    MissionMaker,
    MissionArranger,
)
from .components import Mission
from .components import Preset


class Application(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments or sys.argv[1:])
        self.presets: list[Preset] = []
        self.sources: list[Path] = []
        self.missions: list[Mission] = []

    def start(self):
        appenv.load_arguments(self.sys_arguments)
        appenv.start()
        appenv.show_banner()
        return self

    def stop(self):
        appenv.whisper("Bye ~")
        appenv.stop()

    @override
    def __exit__(self, exc_type, exc_val, exc_tb):
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            appenv.whisper("程序正常退出。")
        elif exc_type is SafeError:
            appenv.say(exc_val)
            result = True
        return result

    @staticmethod
    def export_example_preset(filename: Path):
        filename = Path(PathUtils.force_suffix(filename, ".toml"))
        if filename.exists():
            if appenv.context.force_overwrite and not appenv.context.force_no_overwrite:
                appenv.say("文件已存在，[red]将覆盖目标文件！[/red]")
            else:
                appenv.say("[red]文件已存在[/red]，请指定其它文件名！")
                return

        with importlib.resources.open_text(
            "media_killer", "example_preset.toml"
        ) as example:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(example.read())

        appenv.say(f"已生成示例配置文件：{filename}。[red]请在修改后使用！[/red]")

    def _set_presets_and_sources(self, presets, sources):
        preset_count = len(presets)
        if preset_count == 0:
            raise SafeError("未发现任何配置文件，无法进行任何处理。")

        # 去除重复的配置文件
        preset_ids = set()
        for p in presets:
            if p.id in preset_ids:
                appenv.say(
                    "[red]发现重复的配置文件: [/red][bright_black]{}[/]".format(p.path)
                )
                continue
            preset_ids.add(p.id)
            self.presets.append(p)

        appenv.whisper(
            DynamicColumns(RichDetailPanel(x, title=x.id) for x in self.presets)
        )

        source_count = len(sources)
        if source_count == 0:
            raise SafeError("用户未指定任何来源，无需进行任何处理。")
        self.sources += list(sources)
        appenv.whisper(IndexedListPanel(self.sources, "来源路径列表"))

        appenv.say(
            "已发现{preset_count}个配置文件和{source_count}个来源路径。".format(
                preset_count=preset_count, source_count=source_count
            )
        )

    def _sort_and_set_missions(self, missions):
        self.missions = list(MissionArranger(missions, appenv.context.sort_mode))
        old_count, new_count = len(missions), len(self.missions)
        if old_count != new_count:
            appenv.say(
                "[red]已自动过滤掉{}个重复任务，共{}个任务需要执行。[/red]".format(
                    old_count - new_count, new_count
                )
            )
        else:
            appenv.say("全部任务整理完毕，已按照设定方式排序。")

    def run(self):
        if appenv.context.generate:
            for s in appenv.context.inputs:
                s = Path(s)
                suffix = s.suffix
                if suffix == ".toml" or suffix == "":
                    self.export_example_preset(s)
                else:
                    appenv.whisper(
                        "{filename} 并非合法的文件名，不予处理。".format(filename=s)
                    )
            return

        with InputScanner(appenv.context.inputs) as input_scanner:
            presets, sources = input_scanner.scan()

        self._set_presets_and_sources(presets, sources)

        # missions = MissionMaker.auto_make_missions_multitask(self.presets, self.sources)
        missions = asyncio.run(
            MissionMaker.auto_make_missions(self.presets, self.sources)
        )
        self._sort_and_set_missions(missions)

        for m in self.missions:
            runner = MissionRunner(m)
            runner.run()
