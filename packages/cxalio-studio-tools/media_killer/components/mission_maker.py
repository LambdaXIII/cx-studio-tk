import threading
import time
from collections.abc import Sequence, Generator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rich.columns import Columns
from rich.text import Text

from cx_tools_common.rich_gadgets import (
    RichLabel,
    IndexedListPanel,
    MultiProgressManager,
)
from .argument_group import ArgumentGroup
from .mission import Mission
from .preset import Preset
from .preset_tag_replacer import PresetTagReplacer
from .source_expander import SourceExpander
from ..appenv import appenv


class MissionMaker:
    _lock = threading.Lock()

    def __init__(self, preset: Preset):
        self._preset = preset
        self._source_expander = SourceExpander(self._preset)

    def make_mission(self, source: Path) -> Mission:
        # TODO: add support for cusomizing output dir
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

    def expand_sources(self, sources: Sequence[str | Path]) -> Generator[Path]:
        yield from self._source_expander.expand(*sources)

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
        progressMgr = MultiProgressManager()
        workers = []

        def work(preset: Preset, sources: Sequence[str | Path]) -> list[Mission]:
            task_key = preset.id
            appenv.whisper("开始为预设<{}>扫描源文件并创建任务…".format(preset.name))
            progressMgr.update_task(
                task_key,
                visible=True,
                description="[cyan]<{}>[/cyan]".format(preset.name),
            )

            missions = []
            maker = MissionMaker(preset)
            expanded_sources = list(maker.expand_sources(sources))
            total = len(expanded_sources)
            progressMgr.update_task(task_key, total=total)

            for s in expanded_sources:
                if appenv.really_wanna_quit:
                    appenv.say(
                        "用户中断，[red]未为预设[cyan]{}[/]生成全部任务[/red]".format(
                            preset.name
                        )
                    )
                    break
                m = maker.make_mission(Path(s))
                missions.append(m)
                progressMgr.advance(task_key)
                appenv.pretending_sleep(0.02)
            maker.report(missions)
            progressMgr.update_task(task_key, visible=False)
            return missions

        total_task = appenv.progress.add_task(
            "为{}个预设生成任务…".format(len(presets)), total=None
        )
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for preset in presets:
                worker = executor.submit(work, preset, sources)
                workers.append(worker)
                progressMgr.add_task(preset.id, appenv.progress.add_task(preset.name))
            while not all([w.done() for w in workers]):
                time.sleep(0.1)
                if appenv.wanna_quit:
                    for w in workers:
                        w.cancel()
                    # break
                for task_key in progressMgr.keys():
                    tid, tstatus = progressMgr.get(task_key)
                    if tid:
                        appenv.progress.update(
                            tid,
                            description=tstatus.description,
                            completed=tstatus.completed,
                            total=tstatus.total,
                            visible=tstatus.visible,
                        )
                    current, total = progressMgr.get_total_progress()
                    appenv.progress.update(total_task, completed=current, total=total)

            for w in workers:
                missions.extend(w.result())

            for task_id in progressMgr.task_ids():
                appenv.progress.remove_task(task_id)

        appenv.progress.remove_task(total_task)
        return missions
