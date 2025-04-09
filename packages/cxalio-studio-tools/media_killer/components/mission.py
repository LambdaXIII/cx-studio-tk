from dataclasses import dataclass, field
from pathlib import Path

from rich.text import Text

from cx_studio.utils import PathUtils, FunctionalUtils
from cx_tools_common.rich_gadgets import RichLabel
from .argument_group import ArgumentGroup
from .preset import Preset
from cx_studio.utils import TextUtils
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

    def __rich_detail__(self):
        yield "名称", self.name
        yield "来源预设", RichLabel(self.preset)
        yield "来源文件路径", self.source
        yield "标准目标路径", self.standard_target
        yield "覆盖已存在的目标", "是" if self.overwrite else "否"
        yield "硬件加速模式", self.hardware_accelerate
        yield "额外通用执行参数", self.options
        yield "媒体输入组", self.inputs
        yield "媒体输出组", self.outputs

        cmd_preview = ["(ffmpeg)"]
        cmd_preview.extend(self.options.iter_arguments())
        cmd_preview.append("-hdacel")
        cmd_preview.append(self.hardware_accelerate)
        for input_group in self.inputs:
            cmd_preview.append("-i")
            cmd_preview.append(TextUtils.auto_quote(str(input_group.filename)))
            cmd_preview.extend(input_group.iter_arguments())
        for output_group in self.outputs:
            cmd_preview.extend(output_group.iter_arguments())
            cmd_preview.append(TextUtils.auto_quote(str(output_group.filename)))
        yield "命令参数预览", " ".join(cmd_preview)
