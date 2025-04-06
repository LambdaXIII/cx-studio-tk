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


class MissionMaker:
    def __init__(self, preset: Preset):
        self._preset = preset
        self._task_id = appenv.progress.add_task(
            "为[yellow]<{}>[/yellow]生成任务…".format(self._preset.name),
            visible=False,
            total=None,
        )
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

    def __enter__(self):
        appenv.progress.update(self._task_id, visible=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        appenv.progress.stop_task(self._task_id)

    def __del__(self):
        appenv.progress.remove_task(self._task_id)

    def __make_report(self, n: int):
        preset_label = RichLabel(self._preset, justify="left", overflow="crop")
        missions = Text(f"{n}个任务", style="italic", justify="right")
        return Columns([preset_label, missions], expand=True)

    def auto_make_missions(self, sources: Sequence[str | Path]) -> Generator[Mission]:
        missions = []
        appenv.whisper("开始为预设<{}>扫描源文件并创建任务…".format(self._preset.name))
        for source in appenv.progress.track(sources, task_id=self._task_id):
            source = Path(source)
            for ss in self._source_expander.expand(source):
                if appenv.wanna_quit:
                    break
                m = self.make_mission(ss)
                appenv.whisper(m)
                missions.append(m)
                time.sleep(0.2)
                yield m
        appenv.say(self.__make_report(len(missions)))
        appenv.whisper(
            IndexedListPanel(
                missions,
                title="预设 [red]{}[/red] 生成的任务列表".format(self._preset.name),
            )
        )
