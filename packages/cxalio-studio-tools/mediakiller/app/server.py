from dataclasses import dataclass

from cx_studio.core import DataPackage


@dataclass
class AppContext:
    presets = []
    sources = []
    script_output = None
    pretending_mode = False
    debug = False
    sort_mode = "x"
    continue_mode = False

    def __rich_repr__(self):
        yield "Presets", self.presets
        yield "Sources", self.sources
        yield "ExportScript", self.script_output
        yield "Sort Mode", self.sort_mode
        if self.pretending_mode:
            yield "Pretending Mode"
        if self.debug:
            yield "Debug Mode"
        if self.continue_mode:
            yield "Continue last task"


class App:
    app_name = "MediaKiller"
    app_version = "0.5.0"

    def __init__(self):
        self.context = AppContext()


app = App()
