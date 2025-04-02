from .appserver import server
from .components import Preset
from pathlib import Path
import importlib.resources


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
        filename = Path(filename)
        with importlib.resources.open_text(
            "media_killer", "example_preset.toml"
        ) as example:
            with open(filename, "w") as f:
                f.write(example.read())

    def run(self):
        if server.context.generate:
            self.export_example_preset(server.context.generate)
            server.say(f"已生成示例配置文件：{server.context.generate}")
            return

        presets = []
        for preset_path in server.context.presets:
            server.whisper(f"Reading preset file: {preset_path}")
            preset = Preset.load(preset_path)
            server.say(f"发现配置文件：{preset.name}")
            server.whisper(preset)
            presets.append(preset)
