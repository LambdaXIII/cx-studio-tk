"""Mission 转码任务通用契约。

本模块是 media_killer 共享底座的一部分，定义执行一次转码所需的最小自洽值对象。
Mission 构造完成后不再引用 Preset 或 SourceExpander，可被任何执行单元消费。

内容：
- InputSpec / OutputSpec：Mission 的输入/输出文件规格，frozen dataclass，
  描述文件路径及其专属 FFmpeg 选项。所有路径在构造前必须解析为绝对路径。
- Mission：转码任务值对象，frozen dataclass。包含 ffmpeg 可执行文件、
  源文件、标准目标文件、覆盖标志、硬件加速、全局选项、输入/输出规格列表，
  以及可选的 preset_id/preset_name 展示元数据。
"""

from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path

import ulid

from cx_studio.collectiontools import iter_with_separator
from cx_studio.filesystem import PathUtils
from cx_tools.i18n import _
from cx_wealthy import rich_types as r


@dataclass(frozen=True)
class InputSpec:
    """输入文件规格。

    Attributes:
        filename: 输入文件的绝对路径
        options: 该输入文件的专属选项列表
    """

    filename: Path
    options: list[str]


@dataclass(frozen=True)
class OutputSpec:
    """输出文件规格。

    Attributes:
        filename: 输出文件的绝对路径
        options: 该输出文件的专属选项列表
    """

    filename: Path
    options: list[str]


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
    options: list[str]
    inputs: list[InputSpec]
    outputs: list[OutputSpec]
    preset_id: str | None = None
    preset_name: str | None = None

    def __post_init__(self) -> None:
        """构造后处理：静默移除 options 中的 -y/-n。

        覆盖策略由 Mission.overwrite 字段统一表达，不走此途径。
        """
        filtered = [o for o in self.options if o not in ("-y", "-n")]
        if len(filtered) != len(self.options):
            object.__setattr__(self, "options", filtered)

    @property
    def name(self) -> str:
        """返回源文件名（不含扩展名）。"""
        return PathUtils.get_basename(self.source)

    def __rich__(self) -> r.Text:
        """渲染 Mission 的完整标识行。"""
        return r.Text.assemble(
            *[
                x if isinstance(x, r.Text) else r.Text.from_markup(x)
                for x in iter_with_separator(self.__rich_label__(), " ")
            ],
            overflow="crop",
        )

    def __rich_label__(self) -> Generator[r.RenderableType, None, None]:
        """生成 Mission 标识行的多色片段。"""
        yield r.Text.from_markup(f"[cx.mk.mission.id]{self.mission_id}[/]")
        if self.preset_name:
            yield r.Text.from_markup(f"[cx.mk.mission.preset]{self.preset_name}[/]")
        else:
            yield r.Text.from_markup(f"[cx.mk.mission.preset]{self.preset_id}[/]")
        yield f"[cx.mk.mission.source]({self.source.parent})[/]"

    def __rich_detail__(self) -> Generator[tuple[str, object], None, None]:
        """生成 Mission 的详情面板。"""
        yield _("任务 ID"), str(self.mission_id)
        yield _("源文件"), str(self.source)
        yield _("目标文件"), str(self.standard_target)
        if self.preset_id:
            yield _("预设 ID"), self.preset_id
        if self.preset_name:
            yield _("预设名称"), self.preset_name
        yield _("覆盖模式"), _("是") if self.overwrite else _("否")
        yield _("全局选项"), " ".join(self.options) if self.options else _("无")
        yield _("输入数量"), str(len(self.inputs))
        yield _("输出数量"), str(len(self.outputs))

    def iter_arguments(self) -> Generator[str, None, None]:
        """生成 FFmpeg 命令行参数。

        注意：不包含 ``-y``/``-n`` 覆盖标志。``Mission.__post_init__``
        在构造时已将其从 ``options`` 中滤除。覆盖策略完全由
        ``Mission.overwrite`` 字段表达，由 ``MissionExecutor`` 的
        SKIPPED 语义在 FFmpeg 启动前处理。
        """
        # 全局选项
        yield from self.options

        # 输入文件
        for input_spec in self.inputs:
            yield from input_spec.options
            yield "-i"
            yield str(input_spec.filename)

        # 输出文件
        for output_spec in self.outputs:
            yield from output_spec.options
            yield str(output_spec.filename)

    def __eq__(self, value: object) -> bool:
        """按 (source, preset_id) 判等，用于去重。"""
        if not isinstance(value, Mission):
            return NotImplemented
        return self.source == value.source and self.preset_id == value.preset_id

    def __hash__(self) -> int:
        """按 (source, preset_id) 哈希，用于去重。"""
        return hash((self.source, self.preset_id))
