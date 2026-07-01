"""cx-wealthy: Rich 终端结构化文档与 UI 组件库。

本包是 cx-wealth 的继任者。完整设计文档见根目录 DESIGN.md。
"""

__version__ = "0.1.0"

from .columns import MaxColumnsLayout
from .detail import RichDetailMixin, WealthDetailPanel, WealthDetailTable
from .document import Group, Node, Note, WealthyDocument
from .help import Action, WealthyHelp
from .indexed_list import IndexedListPanel
from .label import RichLabel, RichLabelMixin
from .theme import CX_STYLES, HELP_STYLES, default_theme
from .tutorial import render_tutorial
from . import rich_types

__all__ = [
    # 协议层
    "RichLabelMixin",
    "RichLabel",
    "RichDetailMixin",
    "WealthDetailTable",
    "WealthDetailPanel",
    # 通用文档
    "Node",
    "Group",
    "Note",
    "WealthyDocument",
    # 帮助特化
    "Action",
    "WealthyHelp",
    # 组件
    "IndexedListPanel",
    "MaxColumnsLayout",
    # 教程
    "render_tutorial",
    # 主题
    "CX_STYLES",
    "HELP_STYLES",
    "default_theme",
    # 对外便利
    "rich_types",
]
