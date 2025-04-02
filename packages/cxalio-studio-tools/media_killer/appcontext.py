from dataclasses import dataclass


@dataclass
class AppContext:
    presets = []
    sources = []
    script_output = None
    pretending_mode = False
    debug = False
    sort_mode = "x"
    continue_mode = False
    generate = None
    tutorial = False

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
