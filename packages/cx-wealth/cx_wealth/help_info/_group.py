from __future__ import annotations
from typing import Self, override
from collections.abc import Generator

from cx_wealth._rich import Text
from ._action import _Action
from ._node import _Node
from typing import Literal
from .. import _rich as r


class _Group(_Node):
    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        parent: _Node | None = None,
    ) -> None:
        super().__init__(name, description, parent)

    def add_action(
        self,
        *flags,
        name: str | None = None,
        description: str | None = None,
        metavar: str | None = None,
        nargs: int | Literal["?", "+", "*"] | None = None,
        optional: bool | None = None,
    ) -> _Action:
        action = _Action(
            *flags,
            name=name,
            description=description,
            metavar=metavar,
            nargs=nargs,
            optional=optional,
            parent=self,
        )
        return action

    def add_group(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> _Group:
        group = _Group(name, description, self)
        return group

    def iter_actions(self) -> Generator[_Action, None, None]:
        for action in self.children:
            if isinstance(action, _Action):
                yield action
            elif isinstance(action, _Group):
                yield from action.iter_actions()

    @override
    def render_useage(self) -> Text:
        useages = [x.render_useage() for x in self.iter_actions()]
        return r.Text(" ").join(useages)

    @override
    @r.group(True)
    def render_details(self):
        if self.name:
            yield r.Text(self.name, style="cx.help.group.title")
        if self.description:
            yield r.Text("\t") + r.Text(
                self.description, style="cx.help.group.description"
            )
        for child in self.children:
            p = r.Padding(child.render_details(), (0, 0, 0, child.level))
            yield p
