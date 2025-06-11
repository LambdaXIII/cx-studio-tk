from cx_tools.app import IApplication
from collections.abc import Sequence
import sys
from .appenv import appenv
from .appcontext import AppContext
from cx_wealth import rich_types as r
from cx_wealth import WealthDetailPanel, WealthDetail, WealthLabel, IndexedListPanel

from .components.filter_chain_builder import FilterChainBuilder
from .components.mission import SimpleMissionBuilder, Mission
from .components.mission_runner import MissionRunner

import asyncio


class JpeggerApp(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments or sys.argv[1:])

    def start(self):
        appenv.context = AppContext.from_arguments(self.sys_arguments)
        appenv.start()

    def stop(self):
        appenv.stop()

    def run(self):
        appenv.say(WealthDetailPanel(appenv.context, title="初始化参数"))

        filter_chain = FilterChainBuilder.build_filter_chain_from_simple_context(
            appenv.context
        )

        builder = SimpleMissionBuilder(
            filter_chain,
            appenv.context.output_dir,
            quality=appenv.context.quality,
            target_format=appenv.context.format,
        )

        missions = builder.make_missions(appenv.context.inputs)

        appenv.say(IndexedListPanel([WealthLabel(x) for x in missions]))

        runner = MissionRunner(missions)
        runner.run()
