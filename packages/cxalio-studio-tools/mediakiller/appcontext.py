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
    force_overwrite = False
    force_no_overwrite = False

    def __rich_repr__(self):
        yield from self.__dict__.items()
