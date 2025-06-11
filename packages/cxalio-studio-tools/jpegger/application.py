from cx_tools.app import IApplication
from collections.abc import Sequence
import sys
from .appenv import appenv
from .appcontext import AppContext
from cx_wealth import rich_types as r
from cx_wealth import WealthDetailPanel, WealthDetail


class JpeggerApp(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments or sys.argv[1:])

    def start(self):
        appenv.context = AppContext.from_arguments(self.sys_arguments)
        appenv.start()

    def stop(self):
        appenv.stop()

    def run(self):
        appenv.say(WealthDetailPanel(appenv.context))
