from collections.abc import Iterable, Sequence
import asyncio
import importlib.resources
import sys
from pathlib import Path
from typing import override

from cx_studio.filesystem import force_suffix
from cx_tools.app import IApplication
from cx_wealth import DynamicColumns, IndexedListPanel, WealthDetailPanel
from .appenv import appenv
from .components.exception import SafeError
from .components.input_scanner import InputScanner
from .components.mission import Mission
from .components.mission_arranger import MissionArranger
from .components.mission_maker import MissionMaker
from .components.mission_master import MissionMaster
from .components.mission_xml import MissionXML
from .components.preset import Preset
from .components.script_maker import ScriptMaker
from .mk_help_info import MKHelp


class Application(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None) -> None:
        super().__init__(arguments or sys.argv[1:])
        self.presets: list[Preset] = []
        self.sources: list[Path] = []
        self.missions: list[Mission] = []

    def start(self) -> None:
        appenv.load_arguments(self.sys_arguments)
        appenv.start()
        appenv.show_banner()
        return self  # type: ignore[return]  # 链式调用语法糖，基类契约返回 None

    def stop(self) -> None:
        if not appenv.context.continue_mode:
            self.save_missions(self.missions)
        appenv.whisper("Bye ~")
        appenv.stop()

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> bool:
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            appenv.whisper("程序正常退出。")
        elif exc_type is SafeError:
            appenv.say(exc_val)
            result = True
        return result  # type: ignore[return]  # super().__exit__ 可能返回 None, 但我们的路径保证非 None

    @staticmethod
    def save_missions(missions: list[Mission]):
        mission_xml = MissionXML()
        mission_xml.add_missions(missions)
        mission_xml.save(appenv.config_manager.get_file("last_missions.xml"))

    @staticmethod
    def load_missions() -> list[Mission]:
        last_missions = appenv.config_manager.get_file("last_missions.xml")
        if not last_missions.exists():
            return []
        mission_xml = MissionXML.load(
            appenv.config_manager.get_file("last_missions.xml")
        )
        return list(mission_xml.iter_missions())

    @staticmethod
    def export_example_preset(filename: Path):
        filename = Path(force_suffix(filename, ".toml"))
        appenv.check_overwritable_file(filename)
        with importlib.resources.open_text(
            "media_killer", "example_preset.toml"
        ) as example:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(example.read())

        appenv.say(
            f"[cx.success]已生成示例配置文件：{filename}。[/][blink red]请在修改后使用！[/]"
        )

    def _set_presets_and_sources(
        self, presets: Iterable[Preset], sources: Iterable[Path]
    ) -> None:
        # 去除重复的配置文件
        preset_ids = set()
        for p in presets:
            if p.id in preset_ids:
                appenv.say(f"[cx.warning]发现重复的配置文件: [cx.warning]{p.path}[/]")
                continue
            preset_ids.add(p.id)
            self.presets.append(p)

        appenv.whisper(
            DynamicColumns(WealthDetailPanel(x, title=x.id) for x in self.presets)
        )

        self.sources += list(sources)
        appenv.whisper(IndexedListPanel(self.sources, "来源路径列表"))

        if self.presets or self.sources:
            appenv.say(
                f"已添加 {len(self.presets)} 个配置文件和 {len(self.sources)} 个来源路径。"
            )

    def _sort_and_set_missions(self, missions: Iterable[Mission]) -> None:
        mission_list = list(
            missions
        )  # 转换为 list 以满足 MissionArranger 和 len 的类型要求
        self.missions = list(MissionArranger(mission_list, appenv.context.sort_mode))
        # 检查任务数量并判断是否运行
        if not self.missions:
            raise SafeError("没有任务需要执行。")
        # 汇报任务数量
        old_count, new_count = len(mission_list), len(self.missions)
        if old_count != new_count:
            appenv.say(
                f"[cx.warning]已自动过滤掉 {old_count - new_count} 个重复任务，共 {new_count} 个任务需要执行。[/]"
            )
        else:
            appenv.say("全部任务整理完毕，已按照设定方式排序。")
        appenv.whisper(IndexedListPanel(self.missions, "整理完的任务列表"))

    def run(self) -> None:
        if appenv.context.show_help:
            MKHelp.show_help(appenv.console)
            return

        if appenv.context.show_full_help:
            MKHelp.show_full_help(appenv.console)
            return

        # 是否生成配置文件
        if appenv.context.generate:
            for s in appenv.context.inputs:
                s = Path(s)
                suffix = s.suffix
                if suffix == ".toml" or suffix == "":
                    self.export_example_preset(s)
                else:
                    appenv.whisper(f"{s} 并非合法的文件名，不予处理。")
            return

        # 扫描输入文件
        with InputScanner(appenv.context.inputs) as input_scanner:
            presets, sources = input_scanner.scan()

        self._set_presets_and_sources(presets, sources)

        # 恢复上次的任务
        missions = []
        if appenv.context.continue_mode:
            last_missions = self.load_missions()
            appenv.say(f"从上次执行中恢复了 {len(last_missions)} 个任务……")
            missions.extend(last_missions)

        # 整理并生成任务序列
        output_dir = None
        if appenv.context.output_dir:
            output_dir = Path(appenv.context.output_dir).resolve()
            appenv.say(f'输出目录将被替换为: "{output_dir}"')

        current_missions = asyncio.run(
            MissionMaker.auto_make_missions(
                self.presets,
                self.sources,
                external_output_dir=output_dir,
            )
        )
        if current_missions:
            appenv.say(f"生成了 {len(current_missions)} 个任务。")
        missions.extend(current_missions)
        self._sort_and_set_missions(missions)

        # 生成脚本
        if appenv.context.save_script:
            maker = ScriptMaker(self.missions)
            maker.save(appenv.context.save_script)
            return

        # 执行转码任务
        if appenv.context.pretending_mode:
            appenv.say(
                "[dim]检测到[italic cyan underline]假装模式[/]，将不会真正执行任何操作。[/]"
            )

        mm = MissionMaster(self.missions, appenv.context.max_workers)
        asyncio.run(mm.run())
