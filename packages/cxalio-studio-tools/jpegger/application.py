from cx_tools.app import IApplication
from collections.abc import Sequence
import sys
from .appenv import appenv
from .appcontext import AppContext
from cx_wealth import rich_types as r
from cx_wealth import WealthDetailPanel, WealthDetail, WealthLabel, IndexedListPanel

from .components.filter_chain_builder import FilterChainBuilder
from .components.mission import SimpleMissionBuilder, Mission

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
        filter_chain = FilterChainBuilder.build_filter_chain_from_simple_context(
            appenv.context
        )

        appenv.say(WealthLabel(filter_chain))
        appenv.say(WealthDetailPanel(filter_chain))

        builder = SimpleMissionBuilder(
            filter_chain, appenv.context.output_dir, appenv.context.format
        )

        missions = builder.make_missions(appenv.context.inputs)

        appenv.say(IndexedListPanel([WealthLabel(x) for x in missions]))
