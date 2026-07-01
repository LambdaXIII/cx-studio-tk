"""内容节点。"""

from __future__ import annotations

from typing import override

from rich.console import Group as RichGroup, RenderableType
from rich.padding import Padding
from rich.text import Text

from .node import Node

__all__ = ["Note"]


class Note(Node):
    """内容节点：承载自由文本 / 可渲染内容。

    title 为独立字段，不参与树结构标识；name 仅用于树内寻址。
    """

    def __init__(
        self,
        *contents: RenderableType,
        title: RenderableType | None = None,
        name: str | None = None,
        parent: Node | None = None,
    ) -> None:
        self.title = title
        self.contents = list(contents)
        super().__init__(name=name, parent=parent)

    def add_content(self, content: RenderableType) -> None:
        """追加一段可渲染内容。"""
        self.contents.append(content)

    @override
    def render(self) -> RenderableType:
        """渲染 title（如有）+ contents。"""
        if self.title is None and not self.contents:
            return Text()

        if self.title is None:
            return RichGroup(*self.contents)

        parts: list[RenderableType] = [self.title]
        for content in self.contents:
            parts.append(Padding(content, pad=(0, 0, 0, 4)))
        return RichGroup(*parts)
