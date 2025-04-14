import asyncio
import importlib.resources
import importlib.resources
import sys
from collections.abc import Sequence
from pathlib import Path
from tabnanny import check
from typing import override

from cx_studio.utils import PathUtils
from cx_tools_common.app_interface import IApplication
from media_killer.components.script_maker import ScriptMaker
from .components.exception import SafeError
from cx_wealth import DynamicColumns, IndexedListPanel, RichDetailPanel
from media_killer.components.mission_master import MissionMaster
from .appenv import appenv
from .components import (
    InputScanner,
    MissionMaker,
    MissionArranger,
)
from .components import Mission
from .components import Preset
from .help_info import MKHelpInfo


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
        appenv.check_overwritable_file(filename)
        with importlib.resources.open_text(
            "media_killer", "example_preset.toml"
        ) as example:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(example.read())

        appenv.say(f"已生成示例配置文件：{filename}。[blink red]请在修改后使用！[/]")

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
        if appenv.context.show_help:
            appenv.say(MKHelpInfo())

        # 是否生成配置文件
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

        # 扫描输入文件
        with InputScanner(appenv.context.inputs) as input_scanner:
            presets, sources = input_scanner.scan()

        self._set_presets_and_sources(presets, sources)

        # 整理并生成任务序列
        output_dir = None
        if appenv.context.output_dir:
            output_dir = Path(appenv.context.output_dir).resolve()
            appenv.say('输出目录将被替换为: "{}"'.format(output_dir))

        missions = asyncio.run(
            MissionMaker.auto_make_missions(
                self.presets,
                self.sources,
                external_output_dir=output_dir,
            )
        )
        self._sort_and_set_missions(missions)

        # 生成脚本
        if appenv.context.save_script:
            maker = ScriptMaker(self.missions)
            maker.save(appenv.context.save_script)
            return

        # 执行转码任务
        if appenv.context.pretending_mode:
            appenv.say(
                "[dim]检测到[italic cyan]假装模式[/]，将不会真正执行任何操作。[/]"
            )

        mm = MissionMaster(self.missions, 2)
        asyncio.run(mm.run())
