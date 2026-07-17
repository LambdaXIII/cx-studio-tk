"""容器节点。"""

from __future__ import annotations


from typing import Any, override

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
        detail: str | None = None,
        **kwargs: Any,
    ) -> Group:
        """添加子 Group。
        ``**kwargs`` 可接收 ``titler`` / ``detailer``，
        直接透传给 :class:`Node` 构造器。
        """
        return Group(name=name, detail=detail, parent=self, **kwargs)

    def add_note(
        self,
        *contents: RenderableType,
        title: RenderableType | None = None,
        **kwargs: Any,
    ) -> Note:
        """添加 Note 子节点。

        ``**kwargs`` 可接收 ``titler`` / ``detailer``，透传给 Note。
        """
        return Note(*contents, title=title, parent=self, **kwargs)

    @override
    def _default_titler(self) -> RenderableType | None:
        if self.name is None:
            return None
        return Text(self.name, style="cx.info")

    @override
    def _default_detailer(self) -> RenderableType | None:
        if self.detail is None:
            return None
        return Text(self.detail, style="cx.whisper")

    @override
    def render(self) -> RenderableType:
        """渲染 title（如有）+ description（如有）+ children 的 Group。"""
        parts: list[RenderableType] = []

        if self.title is not None:
            parts.append(self.title)
        if self.description is not None:
            parts.append(self.description)

        for child in self._children:
            parts.append(child.render())

        if not parts:
            return Text()
        if len(parts) == 1:
            return parts[0]
        return RichGroup(*parts)
