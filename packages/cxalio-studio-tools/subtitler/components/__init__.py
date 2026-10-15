"""subtitler 组件子包。

汇集前台的格式接线（`wiring`）与转换编排（`converter`）：接线决定本工具支持
哪些格式，编排把 Loader → Project → Saver 串成一次转换。二者都依赖 appenv，
属于工具特化组件，不进入 `subtitler.common` 能力层。
"""

from .converter import SubtitlerConverter
from .wiring import EXTENSION_TABLE, FORMATS, format_for

__all__ = [
    "EXTENSION_TABLE",
    "FORMATS",
    "SubtitlerConverter",
    "format_for",
]
