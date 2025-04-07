from dataclasses import dataclass, field
from pathlib import Path

from rich.columns import Columns
from rich.text import Text

from cx_studio.utils import PathUtils, FunctionalUtils
from .argument_group import ArgumentGroup
from .preset import Preset
import itertools


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
        return Text.assemble(
            *[
                Text.from_markup(x)
                for x in FunctionalUtils.iter_with_separator(self.__rich_label__(), " ")
            ],
            overflow="crop",
        )

    def __rich_label__(self):
        yield "[bold bright_black]M[/]"
        yield f"[dim green][[cyan]{self.preset.name}[/cyan]:{len(self.inputs)}->{len(self.outputs)}][/dim green]"
        yield f"[yellow]{self.name}[/]"
        yield f"[italic dim blue]({self.source.resolve().parent})[/]"

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Mission):
            return False
        return self.source == value.source and self.preset.id == value.preset.id

    def __hash__(self) -> int:
        return hash(str(self.source)) ^ hash(self.preset) ^ hash("mission")
