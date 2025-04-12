from operator import is_
import re
import threading
import time
from collections.abc import Sequence, Generator, Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from rich.columns import Columns
from rich.text import Text

from cx_tools_common.rich_gadgets import (
    RichLabel,
    IndexedListPanel,
    MultiProgressManager,
    ProgressTaskAgent,
)
from .argument_group import ArgumentGroup
from .mission import Mission
from .preset import Preset
from .preset_tag_replacer import PresetTagReplacer
from .source_expander import SourceExpander
from ..appenv import appenv
import asyncio
import itertools


class MissionMaker:
    _lock = threading.Lock()

    def __init__(self, preset: Preset):
        self._preset = preset
        self._source_expander = SourceExpander(self._preset)

    def make_mission(self, source: Path) -> Mission:
        # TODO: add support for cusomizing output dir
        replacer = PresetTagReplacer(self._preset, source)

        general = ArgumentGroup()
        general.add_options(list(replacer.read_value_as_list(self._preset.options)))

        inputs = []
        for g in self._preset.inputs:
            x = ArgumentGroup()
            x.filename = Path(replacer.read_value(g.filename))
            x.add_options(list(replacer.read_value_as_list(g.options)))
            inputs.append(x)

        outputs = []
        for g in self._preset.outputs:
            x = ArgumentGroup()
            x.filename = Path(replacer.read_value(g.filename))
            x.add_options(list(replacer.read_value_as_list(g.options)))
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

    def expand_sources(self, sources: Iterable[str | Path]) -> Generator[Path]:
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
        wanna_quit = False
        for source in sources:
            source = Path(source)
            for ss in self._source_expander.expand(source):
                if wanna_quit:
                    break
                if appenv.wanna_quit_event.is_set():
                    wanna_quit = True
                    appenv.wanna_quit_event.clear()
                # appenv.whisper(f"\t{ss}")
                m = self.make_mission(ss)
                appenv.pretending_sleep(0.05)
                yield m
                

    @staticmethod
    async def auto_make_missions(
        presets: Iterable[Preset], sources: Iterable[str | Path]
    ) -> list[Mission]:
        missions = []

        async def work(preset: Preset, sources: Iterable[str | Path]) -> list[Mission]:
            result = []
            appenv.whisper("开始为预设<{}>扫描源文件并创建任务…".format(preset.name))
            async with ProgressTaskAgent(
                appenv.progress, task_name=preset.name
            ) as task_agent:
                maker = MissionMaker(preset)
                expanded_sources = list(maker.expand_sources(sources))
                task_agent.set_total(len(expanded_sources))
                task_agent.start()
                for s in expanded_sources:
                    wanna_quit = False
                    if appenv.really_wanna_quit_event.is_set():
                        wanna_quit = True
                        appenv.really_wanna_quit_event.clear()
                    if wanna_quit:
                        appenv.say(
                            "用户中断，[red]未为预设[cyan]{}[/]生成全部任务[/red]".format(
                                preset.name
                            )
                        )
                        break
                    m = maker.make_mission(Path(s))
                    result.append(m)
                    task_agent.advance()
                    await appenv.pretendint_asleep(0.05)
                await asyncio.sleep(2)
                return result

        tasks = []
        for preset in presets:
            task = asyncio.create_task(work(preset, sources))
            tasks.append(task)
            await appenv.pretendint_asleep(0.2)

        results = await asyncio.gather(*tasks)
        missions = list(itertools.chain(*results))

        return missions
