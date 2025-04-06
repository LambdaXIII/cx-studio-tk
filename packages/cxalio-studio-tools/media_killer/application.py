import importlib.resources
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import override

from cx_studio.utils import PathUtils
from cx_tools_common.app_interface import IApplication
from cx_tools_common.exception import SafeError
from cx_tools_common.rich_gadgets import IndexedListPanel
from cx_tools_common.rich_gadgets.dynamic_columns import DynamicColumns
from .appenv import appenv
from .components import InputScanner, SourceExpander
from .components import Preset


class Application(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments or sys.argv[1:])
        self.presets: list[Preset] = []
        self.sources: list[Path] = []

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

    def _check_presets_and_sources(self):
        preset_count = len(self.presets)
        if preset_count == 0:
            raise SafeError("未发现任何配置文件，无法进行任何处理。")

        # appenv.whisper(Columns(self.presets,width=int(appenv.console.width*0.5)-1, equal=True))
        appenv.whisper(DynamicColumns(self.presets))

        source_count = len(self.sources)
        if source_count == 0:
            raise SafeError("用户未指定任何来源，无需进行任何处理。")

        appenv.whisper(IndexedListPanel(self.sources, "来源路径列表"))

        appenv.whisper(
            "已发现{preset_count}个配置文件和{source_count}个来源路径。".format(
                preset_count=preset_count, source_count=source_count
            )
        )

        # appenv.whisper("来源文件如下：")
        # for p in self.presets:
        #     appenv.whisper(p)

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
            self.presets, self.sources = input_scanner.scan()

        self._check_presets_and_sources()
