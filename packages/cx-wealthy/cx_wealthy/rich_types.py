"""Rich 类型便利出口（仅对外使用）。

库内部模块用真实 import 路径（from rich.table import Table）。
本模块仅为使用方提供 `r` 别名约定，收窄到高频类型。
"""

from rich import box, markup, protocol
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.measure import Measurement
from rich.padding import Padding
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style
from rich.table import Column, Table
from rich.text import Text
from rich.theme import Theme

__all__ = [
    "Console",
    "Group",
    "Panel",
    "Table",
    "Column",
    "Text",
    "Style",
    "markup",
    "Markdown",
    "Columns",
    "Align",
    "Padding",
    "box",
    "Theme",
    "Measurement",
    "Segment",
    "protocol",
]
