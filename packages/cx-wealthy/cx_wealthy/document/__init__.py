"""通用结构化文档核心：Node / Group / Note / WealthyDocument。"""

from .document import WealthyDocument
from .group import Group
from .node import Node
from .note import Note

__all__ = ["Node", "Group", "Note", "WealthyDocument"]
