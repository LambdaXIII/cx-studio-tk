"""容器节点。"""

from __future__ import annotations

from collections.abc import Iterator
from typing import override

from rich.console import Group as RichGroup, RenderableType
from rich.text import Text

from .node import Node
from .note import Note

__all__ = ["Group"]


class Group(Node):
    """容器节点：包含一组子节点。"""

    def add_group(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> Group:
        """添加子 Group。"""
        return Group(name=name, description=description, parent=self)

    def add_note(
        self,
        *contents: RenderableType,
        title: RenderableType | None = None,
    ) -> Note:
        """添加 Note 子节点。"""
        return Note(*contents, title=title, parent=self)

    def iter_nodes(self) -> Iterator[Node]:
        """迭代直接子节点（同 iter_children）。"""
        yield from self.iter_children()

    @override
    def render(self) -> RenderableType:
        """渲染 name（如有）+ description（如有）+ children 的 Group。"""
        parts: list[RenderableType] = []

        if self.name:
            parts.append(Text(self.name, style="cx.info"))
        if self.description:
            parts.append(Text(self.description, style="cx.whisper"))

        for child in self._children:
            parts.append(child.render())

        if not parts:
            return Text()
        if len(parts) == 1:
            return parts[0]
        return RichGroup(*parts)
