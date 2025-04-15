from __future__ import annotations

from typing import Self

from .. import rich_types as r


class _Node:
    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        parent: _Node | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.children: list[_Node] = []
        self.parent: _Node | None = None
        self._set_parent(parent)

    def _set_parent(self, parent: _Node | None):
        if self.parent is not None:
            self.parent.children.remove(self)
        self.parent = parent
        if parent is not None and self not in parent.children:
            parent.children.append(self)

    def add_node(self, node: _Node) -> Self:
        node._set_parent(self)
        return self

    def __iter__(self):
        yield from self.children

    @property
    def level(self) -> int:
        return self.parent.level + 1 if self.parent is not None else 0

    def render_usage(self) -> r.Text:
        return r.Text(" ").join(x.render_usage() for x in self.children)

    def render_details(self) -> r.RenderableType:
        return r.Group(*(x.render_details() for x in self.children))
