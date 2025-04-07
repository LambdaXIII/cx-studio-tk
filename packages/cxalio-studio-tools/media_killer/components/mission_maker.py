from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import time
from collections.abc import Sequence, Generator
from pathlib import Path

from rich.columns import Columns
from rich.text import Text

from cx_tools_common.rich_gadgets import RichLabel, IndexedListPanel
from .source_expander import SourceExpander
from .argument_group import ArgumentGroup
from .mission import Mission
from .preset import Preset
from .preset_tag_replacer import PresetTagReplacer
from ..appenv import appenv
from rich.progress import TaskID
import threading


class MissionMaker:
    _lock = threading.Lock()

    def __init__(self, preset: Preset):
        self._preset = preset
        self._source_expander = SourceExpander(self._preset)

    def make_mission(self, source: Path) -> Mission:
        replacer = PresetTagReplacer(self._preset, source)

        general = ArgumentGroup()
        general.add_options(replacer.read_value_as_list(self._preset.options))

        inputs = []
        for g in self._preset.inputs:
            x = ArgumentGroup()
            x.filename = Path(replacer.read_value(g.filename))
            x.add_options(replacer.read_value_as_list(g.options))
            inputs.append(x)

        outputs = []
        for g in self._preset.outputs:
            x = ArgumentGroup()
            x.filename = Path(replacer.read_value(g.filename))
            x.add_options(replacer.read_value_as_list(g.options))
            outputs.append(x)

        return Mission(
            preset=self._preset,
            source=source,
            standard_target=replacer.standard_target,
            overwrite=self._preset.overwrite,
            hardware_accelerate=self._preset.hardware_accelerate or "auto",
            options=general,
            inputs=inputs,
            outputs=outputs,
        )

    def report(self, missions: list):
        with self._lock:
            appenv.whisper(
                IndexedListPanel(
                    missions,
                    title="预设 [red]{}[/red] 生成的任务列表".format(self._preset.name),
                )
            )

            count = len(missions)
            preset_label = RichLabel(self._preset, justify="left", overflow="crop")
            missions_label = Text(f"{count}个任务", style="italic", justify="right")
            appenv.say(Columns([preset_label, missions_label], expand=True))

    def expand_and_make_missions(
        self, sources: Sequence[str | Path]
    ) -> Generator[Mission]:
        # appenv.whisper("开始为预设<{}>扫描源文件并创建任务…".format(self._preset.name))
        for source in sources:
            source = Path(source)
            for ss in self._source_expander.expand(source):
                if appenv.wanna_quit:
                    break
                # appenv.whisper(f"\t{ss}")
                m = self.make_mission(ss)
                appenv.pretending_sleep(0.05)
                yield m

    @staticmethod
    def auto_make_missions_multitask(
        presets: Sequence[Preset],
        sources: Sequence[str | Path],
        max_workers: int | None = None,
    ) -> list[Mission]:
        missions = []
        progresses: dict[str, tuple[int, int | None]] = defaultdict(lambda: (0, None))
        bars: dict[str, TaskID] = {}
        workers = []

        def work(preset: Preset, sources: Sequence[str | Path]) -> list[Mission]:
            missions = []
            total = len(sources)
            maker = MissionMaker(preset)
            appenv.whisper("开始为预设<{}>扫描源文件并创建任务…".format(preset.name))
            for i, s in enumerate(sources, start=1):
                for ss in maker.expand_and_make_missions([s]):
                    missions.append(ss)
                    appenv.pretending_sleep(0.05)
                progresses[preset.name] = (i, total)
            maker.report(missions)
            return missions

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for preset in presets:
                worker = executor.submit(work, preset, sources)
                workers.append(worker)
                bars[preset.name] = appenv.progress.add_task(
                    f"为[yellow]<{preset.name}>[/yellow]生成任务…",
                    total=None,
                    start=True,
                )
            while not all([w.done() for w in workers]):
                time.sleep(0.1)
                if appenv.really_wanna_quit:
                    for w in workers:
                        w.cancel()
                    break
                for p_name, p in progresses.items():
                    i, total = p
                    appenv.progress.update(bars[p_name], total=total, completed=i)
                    # appenv.say(p_name, i, total)

            for w in workers:
                missions.extend(w.result())

            for b in bars.values():
                appenv.progress.remove_task(b)

        return missions
