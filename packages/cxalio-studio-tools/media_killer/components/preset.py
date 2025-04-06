# type: ignore-file

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from cx_studio.core import DataPackage
from cx_studio.utils import PathUtils, TextUtils

DefaultSuffixes = (
    ".mov .mp4 .mkv .avi .wmv .flv .webm "
    ".m4v .ts .m2ts .m2t .mts .m2v .m4v "
    ".vob .3gp .3g2 .f4v .ogv .ogg .mpg "
    ".mpeg .mxf .asf .rm .rmvb .divx "
    ".xvid .h264 .h265 .hevc .vp8 "
    ".vp9 .av1 .avc .avchd .flac .mp3 .wav "
    ".m4a .aac .ogg .wma .flac .alac .aiff "
    ".ape .dsd .pcm .ac3 .dts .eac3 .mp2 "
    ".mpa .opus .mka .mkv .webm .flv .ts .m2ts "
    ".m2t .mts .m2v .m4v .vob .wav .m4a .aac "
    ".ogg .wma .flac .aiff .ape .dsd .pcm "
    ".ac3 .dts .eac3 .mp2 .mpa .opus .mka .mxf_op1a"
)


@dataclass(frozen=True)
class Preset:
    id: str = ""
    name: str = ""
    description: str = ""
    path: Path = Path("")
    ffmpeg: str = "ffmpeg"
    overwrite: bool = False
    hardware_accelerate: str | None = "auto"
    options: str | list = ""
    source_suffixes: set = field(default_factory=set)
    target_suffix: str = ""
    target_folder: Path = Path(".")
    keep_parent_level: int = 0
    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)
    custom: dict = field(default_factory=dict)
    raw: DataPackage = field(default_factory=DataPackage)

    @staticmethod
    def _get_source_suffixes(data: DataPackage) -> set[str]:
        default_suffixes = (
            set(DefaultSuffixes.split())
            if not data.source.ignore_default_suffixes  # type:ignore
            else set()
        )
        includes = {
            PathUtils.normalize_suffix(s)
            for s in TextUtils.auto_list(data.source.suffix_includes)  # type:ignore
        }
        excludes = {
            PathUtils.normalize_suffix(s)
            for s in TextUtils.auto_list(data.source.suffix_excludes)  # type:ignore
        }
        return default_suffixes | includes - excludes

    @classmethod
    def load(cls, filename: Path | str):
        filename = PathUtils.force_suffix(filename, ".toml")
        with open(filename, "rb") as f:
            toml = tomllib.load(f)
        data = DataPackage(**toml)

        return cls(
            id=data.general.preset_id,  # type:ignore
            name=data.general.name,  # type:ignore
            description=data.general.description,  # type:ignore
            path=Path(filename).resolve(),
            ffmpeg=data.general.ffmpeg,  # type:ignore
            overwrite=data.general.overwrite,  # type:ignore
            hardware_accelerate=data.general.hardware_accelerate,  # type:ignore
            options=data.general.options,  # type:ignore
            source_suffixes=Preset._get_source_suffixes(data),
            target_suffix=data.target.suffix,  # type:ignore
            target_folder=data.target.folder,  # type:ignore
            keep_parent_level=data.target.keep_parent_level,  # type:ignore
            inputs=data.input,  # type:ignore
            outputs=data.output,  # type:ignore
            custom=data.custom.to_dict(),  # type:ignore
            raw=data,
        )

    def __rich_console__(self, console, options):
        table = Table(show_header=False, show_footer=False, box=None)
        table.add_column(justify="left")
        table.add_column()
        table.add_column(justify="left", overflow="fold", style="dim blue")

        # table.add_row("预设ID", ":", self.id)
        table.add_row("预设名称", ":", self.name)
        table.add_row("预设描述", ":", self.description)
        table.add_row("预设文件路径", ":", str(self.path))
        table.add_row("FFmpeg路径", ":", self.ffmpeg)
        table.add_row("是否覆盖", ":", str(self.overwrite))
        table.add_row("硬件加速模式", ":", self.hardware_accelerate)
        table.add_row(
            "额外参数",
            ":",
            " ".join(self.options) if isinstance(self.options, list) else self.options,
        )
        table.add_row("源文件扩展名", ":", Columns(self.source_suffixes))
        table.add_row("目标文件扩展名", ":", self.target_suffix)
        table.add_row("目标文件夹", ":", str(self.target_folder))
        table.add_row("保留父级层级", ":", str(self.keep_parent_level))
        table.add_row("输入参数", ":", f"{len(self.inputs)} 组")
        table.add_row("输出参数", ":", f"{len(self.outputs)} 组")
        table.add_row("自定义参数", ":", f"{len(self.custom)} 个")

        rawdata_count = len(self.raw.keys())
        if rawdata_count > 0:
            table.add_row("原始数据", ":", "包含")

        yield Panel(
            table,
            title="[bold]预设ID:[dim red]{}[/dim red]".format(self.id),
            title_align="left",
            # width=min(int(console.width * 0.5), 55),
        )
