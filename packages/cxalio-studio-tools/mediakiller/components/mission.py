from dataclasses import dataclass, field
from pathlib import Path

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
