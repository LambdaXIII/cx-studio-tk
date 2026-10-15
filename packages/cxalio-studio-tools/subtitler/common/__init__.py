"""subtitler 能力层：字幕模型、格式框架与格式实现（对外提供面）。

本包不依赖任何 CLI 组件（appenv/context/前台模块）；工具间复用只允许
指向 ``subtitler.common``。
"""

from .errors import FormatError
from .format import Format
from .loader import SubtitleLoader
from .model import SubtitleItem, SubtitleProject, SubtitleSequence
from .saver import SubtitleSaver
from .timecodec import TimeCodec

from .formats import CsvFormat, SrtFormat, TtmlFormat

__all__ = [
    "CsvFormat",
    "Format",
    "FormatError",
    "SrtFormat",
    "SubtitleItem",
    "SubtitleLoader",
    "SubtitleProject",
    "SubtitleSequence",
    "SubtitleSaver",
    "TimeCodec",
    "TtmlFormat",
]
