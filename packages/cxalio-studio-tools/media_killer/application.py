from ctypes import ArgumentError
import importlib.resources
import logging
import sys
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import ParseResultBytes

from cx_studio.utils import PathUtils
from cx_tools_common.app_interface import IApplication
from .appenv import appenv
from .components import Preset


class Application(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments or sys.argv[1:])
        self.presets: list[Preset] = []
        self.sources: list[Path] = []

    def start(self):
        appenv.load_arguments(self.sys_arguments)
        appenv.start()
        return self

    def stop(self):
        appenv.stop()

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

    def add_input_path(self, path: str | Path):
        filename = Path(path)
        suffix = filename.suffix
        if suffix == ".toml" or suffix == "":
            preset_path = Path(PathUtils.force_suffix(filename, ".toml"))
            if preset_path.exists():
                preset = Preset.load(preset_path)
                appenv.whisper(" {filename} 识别为配置文件。".format(filename=filename))
                appenv.whisper(preset)
                self.presets.append(preset)
            else:
                appenv.whisper(
                    "配置文件 {filename} 不存在。".format(filename=preset_path)
                )
        else:
            appenv.whisper(
                "{filename} 并非配置文件，作为源文件导入。".format(filename=filename)
            )
            self.sources.append(filename)

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

        for p in appenv.context.inputs:
            self.add_input_path(p)

        preset_count = len(self.presets)
        source_count = len(self.sources)
        appenv.whisper(
            "已导入 {preset_count} 个配置文件和 {source_count} 个源文件路径。".format(
                preset_count=preset_count, source_count=source_count
            )
        )

        if preset_count == 0:
            raise ArgumentError("未发现任何配置文件，无法进行任何处理。")
        if source_count == 0:
            raise ArgumentError("未发现任何源文件，无法进行任何处理。")
