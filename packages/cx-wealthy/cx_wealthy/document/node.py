"""通用文档节点基类。"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Self

from rich.console import RenderableType
from rich.text import Text

__all__ = ["Node"]


class Node:
    """通用文档节点基类。

    所有节点（Group / Note / Action）的公共基类。
    提供树结构（children / parent）、层级（level）与渲染钩子。
    """

    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        parent: Node | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.parent: Node | None = None
        self._children: list[Node] = []
        if parent is not None:
            parent.add_child(self)

    @property
    def level(self) -> int:
        """节点层级，根为 0。"""
        if self.parent is None:
            return 0
        return self.parent.level + 1

    def add_child(self, child: Node) -> Self:
        """添加子节点。安全处理从原 parent 移除。"""
        if child.parent is not None and child.parent is not self:
            try:
                child.parent._children.remove(child)
            except ValueError:
                pass
        child.parent = self
        if child not in self._children:
            self._children.append(child)
        return self

    def iter_children(self) -> Iterator[Node]:
        """迭代直接子节点。"""
        return iter(self._children)

    def walk(self) -> Iterator[Node]:
        """深度优先遍历所有后代。带 visited 集合防环。"""
        visited: set[int] = set()

        def _walk(node: Node) -> Iterator[Node]:
            for child in node.iter_children():
                child_id = id(child)
                if child_id in visited:
                    continue
                visited.add(child_id)
                yield child
                yield from _walk(child)

        return _walk(self)

    def render(self) -> RenderableType:
        """渲染本节点。默认返回 children 的 Group 或空 Text。"""
        from rich.console import Group as RichGroup

        if not self._children:
            return Text()
        return RichGroup(*(child.render() for child in self._children))

    def __rich__(self) -> RenderableType:
        return self.render()
