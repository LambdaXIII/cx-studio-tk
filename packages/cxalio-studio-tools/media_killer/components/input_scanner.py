from collections.abc import Collection
from pathlib import Path

from rich.columns import Columns
from rich.text import Text

from cx_studio.utils import PathUtils, FunctionalUtils
from media_killer.appenv import appenv
from .preset import Preset


class InputScanner:
    def __init__(self, inputs: Collection[str | Path]):
        self._inputs: list[str | Path] = list(inputs)
        self._task_id = appenv.progress.add_task("预处理输入项…", visible=False)

    def __enter__(self):
        appenv.progress.update(self._task_id, visible=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        appenv.progress.stop_task(self._task_id)
        appenv.progress.update(self._task_id, visible=False)

        return False

    def __del__(self):
        appenv.progress.remove_task(self._task_id)

    @staticmethod
    def is_preset(path: str | Path) -> bool:
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix == ".toml":
            return True
        if suffix == "":
            p_path = PathUtils.force_suffix(path, ".toml")
            return p_path.exists()
        return False

    def add_inputs(self, *paths) -> "InputScanner":
        for p in FunctionalUtils.flatten_list(*paths):
            self._inputs.append(p)
        return self

    @staticmethod
    def _print_result(source: str | Path, is_preset: bool):
        result = (
            Text("配置文件路径", style="cyan", justify="right")
            if is_preset
            else Text("媒体来源路径", style="green", justify="right")
        )
        path = Text(str(source), style="yellow", justify="left")
        appenv.whisper(Columns([path, result], expand=True))

    def scan(self) -> tuple[list[Preset], list[Path]]:
        presets: list[Preset] = []
        sources: list[Path] = []

        appenv.whisper("检索待处理路径并从中解析配置文件...")

        for input_path in appenv.progress.track(self._inputs, task_id=self._task_id):
            if self.is_preset(input_path):
                preset = Preset.load(input_path)
                presets.append(preset)
                self._print_result(input_path, True)
            else:
                sources.append(Path(input_path))
                self._print_result(input_path, False)

            # time.sleep(0.5)

        return presets, sources
