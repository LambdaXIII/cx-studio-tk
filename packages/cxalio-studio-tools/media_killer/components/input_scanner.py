import time
from media_killer.appenv import appenv

from pathlib import Path
from collections.abc import Collection
from rich.progress import Progress
from cx_tools_common.app_interface import TaskAgent
from cx_studio.utils import PathUtils, FunctionalUtils
from .preset import Preset
from rich.columns import Columns
from rich.text import Text


class InputScanner:
    def __init__(self, inputs: Collection[str | Path]):
        self._inputs: list[str | Path] = list(inputs)
        self._task_id = None

    def __enter__(self):
        self._task_id = appenv.progress.add_task("预处理待处理项…")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._task_id:
            if not appenv.context.debug_mode:
                appenv.progress.update(self._task_id, visible=False)
            appenv.progress.stop_task(self._task_id)
            appenv.progress.remove_task(self._task_id)
            appenv.progress.refresh()
        return False

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
        for input in appenv.progress.track(self._inputs, task_id=self._task_id):
            if self.is_preset(input):
                preset = Preset.load(input)
                presets.append(preset)
                self._print_result(input, True)
            else:
                sources.append(Path(input))
                self._print_result(input, False)
            # time.sleep(0.1)

        return presets, sources
