from cx_tools.app import IApplication
from collections.abc import Sequence
from .appenv import appenv


class LandlordApp(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None):
        super().__init__(arguments)

    def start(self):
        appenv.start()

    def stop(self):
        appenv.stop()

    def run(self):
        appenv.say("Hello, World!")
