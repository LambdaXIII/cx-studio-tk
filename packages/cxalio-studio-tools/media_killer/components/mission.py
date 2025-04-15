from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path

import ulid
from rich.columns import Columns
from rich.text import Text

from cx_studio.utils import FunctionalUtils
from cx_studio.utils import PathUtils
from cx_wealth import WealthLabel
from .argument_group import ArgumentGroup
from .preset import Preset


@dataclass(frozen=True)
class Mission:
    mission_id: ulid.ULID = field(default_factory=ulid.new, kw_only=True)
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

    def iter_arguments(
        self,
        force_overwrite: bool | None = None,
        quote_mode: PathUtils.PathQuoteMode = "none",
    ) -> Generator[str]:
        if self.hardware_accelerate:
            yield "-hwaccel"
            yield self.hardware_accelerate
        overwrite = self.overwrite if force_overwrite is None else force_overwrite
        yield "-y" if overwrite else "-n"
        yield from self.options.iter_arguments()
        for input_group in self.inputs:
            yield from input_group.iter_arguments()
            yield "-i"
            yield PathUtils.quoted(input_group.filename, quote_mode)
        for output_group in self.outputs:
            yield from output_group.iter_arguments()
            yield PathUtils.quoted(output_group.filename, quote_mode)

    def __rich_detail__(self):
        yield "名称", self.name
        yield "来源预设", WealthLabel(self.preset)
        yield "来源文件路径", self.source
        yield "标准目标路径", self.standard_target
        yield "覆盖已存在的目标", "是" if self.overwrite else "否"
        yield "硬件加速模式", self.hardware_accelerate
        if self.options:
            yield "通用参数（自定义）", Columns(
                self.options.iter_arguments(position_for_position_arguments="front")
            )
        yield "媒体输入组", self.inputs
        yield "媒体输出组", self.outputs

        yield "命令参数预览", " ".join(
            ["(ffmpeg)"] + list(self.iter_arguments(quote_mode="force"))
        )

    def iter_output_filenames(self) -> Generator[Path]:
        for output_group in self.outputs:
            if output_group.filename is not None:
                yield output_group.filename

    def iter_input_filenames(self) -> Generator[Path]:
        for input_group in self.inputs:
            if input_group.filename is not None:
                yield input_group.filename
