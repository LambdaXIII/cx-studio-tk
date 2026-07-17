"""cx-wealthy: Rich 终端结构化文档与 UI 组件库。"""

__version__ = "0.9.0"
from .widgets import (
    IndexedListPanel,
    MaxColumnsLayout,
    RichDetailMixin,
    RichLabel,
    RichLabelMixin,
    WealthyDetailPanel,
    WealthyDetailTable,
)
from .tutorial import render_tutorial
from .document import Group, Node, Note, WealthyDocument
from .help import Action, HelpGroup, WealthyHelp
from .theme import (
    BASE_STYLES,
    CX_STYLES,
    DETAIL_STYLES,
    FULL_HELP_STYLES,
    HELP_STYLES,
    INDEXED_LIST_STYLES,
    default_theme,
)
from . import rich_types

__all__ = [
    # 协议层
    "RichLabelMixin",
    "RichLabel",
    "RichDetailMixin",
    "WealthyDetailTable",
    "WealthyDetailPanel",
    # 通用文档
    "Node",
    "Group",
    "Note",
    "WealthyDocument",
    # 帮助特化
    "Action",
    "HelpGroup",
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
