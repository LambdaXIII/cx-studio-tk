"""Mission 值对象定义。

Mission 是完全解析的转码任务契约，构造完成后自洽，不再引用 Preset。
"""

from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path

import ulid

from cx_studio.collectiontools import iter_with_separator
from cx_studio.filesystem import get_basename
from cx_tools.i18n import _
from cx_wealth import rich_types as r
from .specs import InputSpec, OutputSpec


@dataclass(frozen=True)
class Mission:
    """转码任务值对象。

    Mission 是完全解析的 frozen dataclass，所有路径在构造前已解析为绝对路径，
    所有标签在生成阶段已替换完毕。Mission 生成后自洽，不再引用 Preset。

    Attributes:
        mission_id: 唯一任务标识符（ULID）
        ffmpeg: FFmpeg 可执行文件路径（已解析）
        source: 源文件绝对路径
        standard_target: 标准目标文件绝对路径
        overwrite: 是否覆盖已存在的目标
        hardware_accelerate: 硬件加速模式（如 "auto"、"cuda" 等）
        options: 全局 FFmpeg 选项
        inputs: 输入文件规格列表
        outputs: 输出文件规格列表
        preset_id: 来源预设 ID（仅用于展示）
        preset_name: 来源预设名称（仅用于展示）
    """

    mission_id: ulid.ULID = field(default_factory=ulid.new, kw_only=True)
    ffmpeg: str
    source: Path
    standard_target: Path
    overwrite: bool
    hardware_accelerate: str | None
    options: list[str]
    inputs: list[InputSpec]
    outputs: list[OutputSpec]
    preset_id: str | None = None
    preset_name: str | None = None

    @property
    def name(self) -> str:
        """返回源文件名（不含扩展名）。"""
        return get_basename(self.source)

    def __rich__(self) -> r.Text:
        """渲染 Mission 的完整标识行。"""
        return r.Text.assemble(
            *[
                r.Text.from_markup(x)
                for x in iter_with_separator(self.__rich_label__(), " ")
            ],
            overflow="crop",
        )

    def __rich_label__(self) -> Generator[r.RenderableType, None, None]:
        """生成 Mission 标识行的多色片段。

        格式：M [preset_name:inputs->outputs] source_name (source_dir)
        """
        yield "[cx.mk.mission.type]M[/]"
        preset_display = self.preset_name or "unknown"
        yield f"[cx.mk.mission.metadata][{preset_display}:{len(self.inputs)}->{len(self.outputs)}][/]"
        yield f"[cx.mk.mission.name]{self.name}[/]"
        yield f"[cx.mk.mission.source]({self.source.parent})[/]"

    def __rich_detail__(self) -> Generator[tuple[str, object], None, None]:
        """生成 Mission 的详情面板。"""
        yield _("名称"), self.name
        preset_display = (
            f"{self.preset_name}({self.preset_id})" if self.preset_name else "-"
        )
        yield _("来源预设"), preset_display
        yield _("来源文件路径"), self.source
        yield _("标准目标路径"), self.standard_target
        yield _("覆盖已存在的目标"), _("是") if self.overwrite else _("否")
        yield _("硬件加速模式"), self.hardware_accelerate or "-"

        if self.options:
            yield _("全局选项"), " ".join(self.options)

        yield _("输入文件"), ", ".join(str(spec.filename) for spec in self.inputs)
        yield _("输出文件"), ", ".join(str(spec.filename) for spec in self.outputs)

        yield _("命令参数预览"), " ".join(["(ffmpeg)"] + list(self.iter_arguments()))

    def iter_arguments(self) -> Generator[str, None, None]:
        """生成 FFmpeg 命令行参数。

        注意：不向 FFmpeg 传递 -y/-n 参数，由 MissionExecutor 通过临时文件机制控制。

        顺序：
        1. 硬件加速参数
        2. 全局 options
        3. 输入文件组（每个输入的 options + -i + filename）
        4. 输出文件组（每个输出的 options + filename）
        """
        # 1. 硬件加速参数
        if self.hardware_accelerate:
            yield "-hwaccel"
            yield self.hardware_accelerate

        # 2. 全局 options
        yield from self.options

        # 3. 输入文件组
        for input_spec in self.inputs:
            yield from input_spec.options
            yield "-i"
            yield str(input_spec.filename)

        # 4. 输出文件组
        for output_spec in self.outputs:
            yield from output_spec.options
            yield str(output_spec.filename)

    def __eq__(self, value: object) -> bool:
        """按 (source, preset_id) 判等，用于去重。"""
        if not isinstance(value, Mission):
            return False
        return self.source == value.source and self.preset_id == value.preset_id

    def __hash__(self) -> int:
        """按 (source, preset_id) 哈希，用于去重。"""
        return hash((self.source, self.preset_id))
