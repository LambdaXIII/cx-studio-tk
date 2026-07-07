"""Preset 系统子包。

本包承载 Preset 系统的四个模块：
- preset.py：Preset 值对象与 InputTemplate/OutputTemplate
- loader.py：PresetLoader，从 TOML 文件加载并 lint Preset
- tag_replacer.py：PresetTagReplacer，标签替换引擎
- maker.py：MissionMaker，基于 Preset + 源文件生成 Mission
"""

from .loader import PresetLoader
from .maker import MissionMaker
from .preset import (
    DEFAULT_SUFFIXES,
    InputTemplate,
    OutputTemplate,
    Preset,
)
from .tag_replacer import PresetTagReplacer

__all__ = [
    "DEFAULT_SUFFIXES",
    "InputTemplate",
    "MissionMaker",
    "OutputTemplate",
    "Preset",
    "PresetLoader",
    "PresetTagReplacer",
]
