from __future__ import annotations


from . import _rich as r
import argparse
from collections.abc import Sequence, Generator
from dataclasses import dataclass, field
import itertools
from typing import Literal, Self, override
import re, sys

from cx_studio.utils import FunctionalUtils, NumberUtils


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

    def add_child(self, child: _Node) -> Self:
        child.parent = self
        if child not in self.children:
            self.children.append(child)
        return self

    def set_parent(self, parent: _Node | None) -> Self:
        if self.parent is not None:
            self.parent.children.remove(self)
        if parent is not None:
            parent.add_child(self)
        else:
            self.parent = parent

        return self

    def __iter__(self):
        yield self
        for child in self.children:
            yield from child

    def iter_actions(self) -> Generator[_Action]:
        for child in self.children:
            if isinstance(child, _Action):
                yield child
            else:
                yield from child.iter_actions()

    @property
    def level(self) -> int:
        if self.parent is None:
            return 0
        else:
            return self.parent.level + 1

    def add_group(
        self,
        name: str | None = None,
        description: str | None = None,
        mutually_exclusive: bool = False,
    ) -> _Group | _MutuallyExclusiveGroup:
        t = _MutuallyExclusiveGroup if mutually_exclusive else _Group
        group = t(
            name=name,
            description=description,
            parent=self,
        )
        self.add_child(group)
        return group

    def add_action(
        self,
        *flags,
        metavar: str | None = None,
        name: str | None = None,
        description: str | None = None,
        nargs: int | Literal["?", "+", "*"] | None = None,
    ) -> _Action:
        action = _Action(
            *flags,
            metavar=metavar,
            name=name,
            description=description,
            nargs=nargs,
            parent=self,
        )
        self.add_child(action)
        return action


class _Action(_Node):
    __optional_pattern = "[cx.help.useage.bracket][[/]{}[cx.help.useage.bracket]][/]"

    def __init__(
        self,
        *flags,
        metavar: str | None = None,
        name: str | None = None,
        description: str | None = None,
        nargs: int | Literal["?", "+", "*"] | None = None,
        parent: _Node | None = None,
    ) -> None:
        super().__init__(name, description, parent)
        self.flags = [str(x) for x in flags]
        self.metavar = metavar
        self.nargs = nargs

    def is_positional(self) -> bool:
        return not self.flags or all(not re.match(r"^[+-]+\w+", x) for x in self.flags)

    def _argument(self):
        return self.flags[0] if self.flags else self.metavar or self.name or ""


class _Group(_Node):
    pass


class _MutuallyExclusiveGroup(_Node):
    pass


class RichHelpInfo:
    DEFAULT_STYLES = {
        "cx.help.useage.title": "bold green",
        "cx.help.useage.option": "cyan",
        "cx.help.useage.argument": "default",
        "cx.help.useage.bracket": "dim default",
        "cx.help.group.title": "bold yellow",
    }

    def __init__(self, prog: str | None = None, styles: dict | None = None) -> None:
        self.root_node = _Node()
        self.prog = prog or sys.argv[0]
        self.styles = styles or self.DEFAULT_STYLES
        self.theme = r.Theme(self.styles)

    def add_group(
        self,
        name: str | None = None,
        description: str | None = None,
        mutually_exclusive: bool = False,
    ):
        return self.root_node.add_group(
            name=name, description=description, mutually_exclusive=mutually_exclusive
        )

    def add_action(
        self,
        *flags,
        metavar: str | None = None,
        name: str | None = None,
        description: str | None = None,
        nargs: int | Literal["?", "+", "*"] | None = None,
    ):
        return self.root_node.add_action(
            *flags, metavar=metavar, name=name, description=description, nargs=nargs
        )

    @staticmethod
    def _leading_space(n: int) -> str:
        return " " * 2 * n

    def _render_action_form(self, action: _Action) -> str:
        flags = [f"[cyan]{x}[/]" for x in action.flags]
        var = action.metavar or action.name or None
        argument = f" [yellow]{var.upper()}[/]" if var else None
        line = ",".join(flags)
        if argument:
            line += argument
        return line

    def _render_action_useage(self, action: _Action):
        argument = (
            action.flags[0] if action.flags else action.metavar or action.name or None
        )
        arguments = []
        if isinstance(action.nargs, "int"):
            n = int(NumberUtils.limit_number(action.nargs, bottom=1))
            if n == 1:
                arguments.append(argument)
            else:
                for i in range(1, n + 1):
                    arguments.append(f"{argument}{i}")

    def _render_useage(self):
        actions = self.root_node.iter_actions()
        pos, n_pos = FunctionalUtils.split_to_two(actions, lambda x: x.is_positional())

        elements = [x.get_useage() for x in n_pos] + [x.get_useage() for x in pos]

        table = r.Table(show_header=False, box=None)
        table.add_column("prog")
        table.add_column("useage", overflow="fold")
        table.add_row(self.prog, " ".join(elements))
        return r.Panel(table, title="用法", title_align="left")

    @r.group(True)
    def render(self):
        yield self._render_useage()
        for i, element in enumerate(self.root_node):
            if i == 0:
                continue
            element_leading = self._leading_space(element.level)
            if isinstance(element, _Action):
                yield element_leading + self._render_action_form(element)
                yield f"{element_leading}\t{element.description}"
            else:
                yield element_leading + f"[yellow]{element.name}[/]"
                yield element_leading + f"\t[yellow]{element.description}[/]"

    def __rich__(self):
        return self.render()
