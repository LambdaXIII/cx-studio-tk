import importlib.resources
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from cx_studio.utils import PathUtils
from cx_tools_common.app_interface import IApplication
from .appenv import appenv
from .components import Preset


class Application(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments or sys.argv[1:])

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

    def run(self):
        if appenv.context.generate:
            for s in appenv.context.sources:
                s = Path(s)
                suffix = s.suffix
                if suffix == ".toml" or suffix == "":
                    self.export_example_preset(s)
                else:
                    appenv.whisper(
                        "{filename} 并非合法的文件名，不予处理。".format(filename=s)
                    )
            return

        appenv.whisper("Making missions from sources...")
