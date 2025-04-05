from dataclasses import dataclass, field
from pathlib import Path
from turtle import width
from rich.text import Text

from cx_studio.utils import PathUtils
from .argument_group import ArgumentGroup
from .preset import Preset
from rich.columns import Columns


@dataclass(frozen=True)
class Mission:
    preset: Preset
    source: Path
    standard_target: Path
    overwrite: bool = False
    hardware_accelerate: str = "auto"
    options: ArgumentGroup = field(default_factory=ArgumentGroup)
    inputs: list[ArgumentGroup] = field(default_factory=list)
    outputs: list[ArgumentGroup] = field(default_factory=list)

    @property
    def name(self):
        return PathUtils.get_basename(self.source)

    def __rich_console__(self, console, _options):
        title = Text("M")
        name = Text(self.name, style="bold yellow", justify="left")
        io_count = Text(
            "[{}->{}]".format(len(self.inputs), len(self.outputs)),
            style="green",
            justify="left",
        )
        folder = Text(
            f"({self.source.resolve().parent})",
            style="italic",
            justify="right",
            no_wrap=True,
            overflow="fold",
        )
        empty = Text("\t", tab_size=100, overflow="crop")
        yield Columns([title, io_count, name, folder])
