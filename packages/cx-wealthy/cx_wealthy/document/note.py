"""内容节点。"""

from __future__ import annotations

from typing import Any, override


from rich.console import Group as RichGroup, RenderableType
from rich.padding import Padding
from rich.text import Text

from .node import Node

__all__ = ["Note"]


class Note(Node):
    """内容节点：承载自由文本 / 可渲染内容。

    ``title`` 参数是便利构造器，会被转成 ``titler`` 渲染器。
    若调用方同时传入 ``titler`` 与 ``title``，则 ``titler`` 优先，
    ``title`` 被忽略。``name`` 仅用于树内寻址。
    """

    def __init__(
        self,
        *contents: RenderableType,
        title: RenderableType | None = None,
        name: str | None = None,
        detail: str | None = None,
        parent: Node | None = None,
        **kwargs: Any,
    ) -> None:
        self.contents = list(contents)
        if title is not None and "titler" not in kwargs:
            _t = title
            kwargs["titler"] = lambda: _t
        super().__init__(name=name, detail=detail, parent=parent, **kwargs)

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
