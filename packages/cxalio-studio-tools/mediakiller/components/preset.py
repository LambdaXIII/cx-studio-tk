# type: ignore-file

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

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
        filename = Path(filename)
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

    def __rich_repr__(self):
        yield from self.__dict__.items()
