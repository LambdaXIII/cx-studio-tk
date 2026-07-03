"""cx-wealthy: Rich 终端结构化文档与 UI 组件库。"""

__version__ = "0.1.1"

from .columns import MaxColumnsLayout
from .detail import RichDetailMixin, WealthDetailPanel, WealthDetailTable
from .document import Group, Node, Note, WealthyDocument
from .help import Action, ActionGroup, WealthyHelp
from .indexed_list import IndexedListPanel
from .label import RichLabel, RichLabelMixin
from .theme import (
    BASE_STYLES,
    CX_STYLES,
    DETAIL_STYLES,
    FULL_HELP_STYLES,
    HELP_STYLES,
    INDEXED_LIST_STYLES,
    default_theme,
)
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
    "ActionGroup",
    "WealthyHelp",
    # 组件
    "IndexedListPanel",
    "MaxColumnsLayout",
    # 教程
    "render_tutorial",
    # 主题
    "BASE_STYLES",
    "CX_STYLES",
    "HELP_STYLES",
    "DETAIL_STYLES",
    "INDEXED_LIST_STYLES",
    "FULL_HELP_STYLES",
    "default_theme",
    # 对外便利
    "rich_types",
]
