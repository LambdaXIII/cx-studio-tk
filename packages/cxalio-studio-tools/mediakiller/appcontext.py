from dataclasses import dataclass

APP_NAME = "MediaKiller"
APP_VERSION = "0.5.0"


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

    @property
    def app_name(self):
        return APP_NAME

    @property
    def app_version(self):
        return APP_VERSION
