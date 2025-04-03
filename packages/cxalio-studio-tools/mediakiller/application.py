from .appserver import server
from .components import Preset
from pathlib import Path
import importlib.resources
from cx_studio.utils import PathUtils


class Application:
    def __init__(self):
        pass

    def __enter__(self):
        server.start_environment()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        server.stop_environment()
        return False

    @staticmethod
    def export_example_preset(filename: Path):
        filename = Path(PathUtils.force_suffix(filename, ".toml"))
        if filename.exists():
            if (
                server.context.force_overwrite  # type:ignore
                and not server.context.force_no_overwrite  # type:ignore
            ):
                server.say("文件已存在，[red]将覆盖目标文件！[/red]")
            else:
                server.say("[red]文件已存在[/red]，请指定其它文件名！")
                return

        with importlib.resources.open_text(
            "mediakiller", "example_preset.toml"
        ) as example:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(example.read())

        server.say(
            f"已生成示例配置文件：[yellow]{filename}[yellow]。[red]请在修改后使用！[/red]"
        )

    def run(self):
        if server.context.generate:  # type:ignore
            self.export_example_preset(server.context.generate)  # type:ignore
            return

        server.whisper("Scanning preset files")
        presets = []
        for preset_path in server.context.presets:  # type:ignore
            preset_path = Path(PathUtils.force_suffix(preset_path, ".toml"))
            server.whisper(f"Reading preset file: {preset_path}")
            preset = Preset.load(preset_path)
            server.whisper(preset)
            presets.append(preset)

        server.whisper("Making missions from sources...")
