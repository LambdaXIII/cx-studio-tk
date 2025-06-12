from __future__ import annotations

from collections.abc import Generator
from typing import override

from cx_wealth.rich_types import Text
from ._action import _Action, _ActionNargs
from ._node import _Node
from .. import rich_types as r


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
        nargs: int | _ActionNargs | None = None,
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
    def render_usage(self) -> Text:
        usages = [x.render_usage() for x in self.iter_actions()]
        return r.Text(" ").join(usages)

    @override
    @r.group(True)
    def render_details(self):
        if self.name:
            yield r.Padding(
                r.Text(self.name, style="cx.help.group.title"), pad=(1, 0, 0, 0)
            )
        if self.description:
            yield r.Padding(
                r.Text(
                    self.description, style="cx.help.group.description", overflow="fold"
                ),
                pad=(0, 0, 0, 2),
            )
        for child in self.children:
            p = r.Padding(child.render_details(), (0, 0, 1, child.level))
            yield p
