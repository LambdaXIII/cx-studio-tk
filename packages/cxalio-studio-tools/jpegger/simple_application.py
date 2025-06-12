import sys
from collections.abc import Sequence

from cx_tools.app import IApplication
from cx_wealth import WealthDetailPanel, WealthLabel, IndexedListPanel
from .appenv import appenv
from .components.mission_runner import MissionRunner
from .simple_appcontext import SimpleAppContext, SimpleHelp
from .simple_filter_chain_builder import SimpleFilterChainBuilder
from .simple_mission_builder import SimpleMissionBuilder


class JpeggerApp(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments or sys.argv[1:])

    def start(self):
        appenv.context = SimpleAppContext.from_arguments(self.sys_arguments)
        appenv.start()

    def stop(self):
        appenv.stop()

    def run(self):
        if appenv.context.show_help:
            appenv.say(SimpleHelp())
            return

        appenv.whisper(WealthDetailPanel(appenv.context, title="初始化参数"))

        filter_chain = SimpleFilterChainBuilder.build_filter_chain_from_simple_context(
            appenv.context
        )

        appenv.whisper(WealthDetailPanel(filter_chain, title="过滤器链"))

        builder = SimpleMissionBuilder(filter_chain, appenv.context)

        missions = builder.make_missions(appenv.context.inputs)

        appenv.whisper(
            IndexedListPanel([WealthLabel(x) for x in missions], title="任务列表")
        )

        runner = MissionRunner(missions)
        runner.run()
