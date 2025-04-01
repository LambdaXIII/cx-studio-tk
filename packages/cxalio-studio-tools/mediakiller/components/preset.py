from dataclasses import dataclass

from pathlib import Path
import tomllib
from typing import Any
from cx_studio.utils import PathUtils


@dataclass
class Preset:
    id: str
    name: str
    description: str
    ffmpeg: str
    overwite: bool = False
    hardware_accelerate: str = "auto"
    source_suffixes: set = set()
    target_suffix: str
    target_folder: Path
    keep_parent_level: int = 0
    inputs: list = []
    outputs: list = []


class PresetLoader:
    DefaultSuffixes = ".mov .mp4 .mkv .avi .wmv .flv .webm .m4v .ts .m2ts .m2t .mts .m2v .m4v .vob .3gp .3g2 .f4v .ogv .ogg .mpg .mpeg .mxf .asf .rm .rmvb .divx .xvid .h264 .h265 .hevc .vp8 .vp9 .av1 .avc .avchd .flac .mp3 .wav .m4a .aac .ogg .wma .flac .alac .aiff .ape .dsd .pcm .ac3 .dts .eac3 .mp2 .mpa .opus .mka .mkv .webm .flv .ts .m2ts .m2t .mts .m2v .m4v .vob .wav .m4a .aac .ogg .wma .flac .alac .aiff .ape .dsd .pcm .ac3 .dts .eac3 .mp2 .mpa .opus .mka"

    def __init__(self, data: dict[str, Any] = None):
        self._data = data or {}
