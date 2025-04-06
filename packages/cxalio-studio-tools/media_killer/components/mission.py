from dataclasses import dataclass, field
from pathlib import Path

from rich.columns import Columns
from rich.text import Text

from cx_studio.utils import PathUtils
from .argument_group import ArgumentGroup
from .preset import Preset


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

    def __rich__(self):
        return Columns([Text.from_markup(x) for x in self.__rich_label__()])

    def __rich_label__(self):
        yield "[bold bright_black]M[/]"
        yield f"[yellow]{self.name}[/]"
        yield f"[italic dim blue]({self.source.resolve().parent})[/]"
        yield f"[green][[cyan]{self.preset.name}[/cyan]:{len(self.inputs)}->{len(self.outputs)}][/green]"
