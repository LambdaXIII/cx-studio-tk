from __future__ import annotations
import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Self
import re,sys

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
        for child in self.children:
            yield from child

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
    ) -> _Group:
        group = _Group(name, description, mutually_exclusive, self)
        self.add_child(group)
        return group

    def add_action(
        self,
        *flags,
        metavar: str | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> _Action:
        action = _Action(*flags, metavar, name, description, self)
        self.add_child(action)
        return action


class _Action(_Node):
    def __init__(
        self,
        *flags,
        metavar: str | None = None,
        name: str | None = None,
        description: str | None = None,
        parent: _Node | None = None,
    ) -> None:
        super().__init__(name, description, parent)
        self.flags = [str(x) for x in flags]
        self.metavar = metavar

    def is_positional(self) -> bool:
        return all(re.match(r"^[+-]", x) for x in self.flags)


class _Group(_Node):
    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        mutually_exclusive: bool = False,
        parent: _Node | None = None,
    ) -> None:
        super().__init__(name, description, parent)
        self.mutually_exclusive = mutually_exclusive


class RichHelpInfo:
    DEFAULT_THEME = {
        "cx.usage.title": "bold blue",
        "cx.usage.positional": "bold blue",
        "cx.usage.program": "bold blue",
        "cx.useage.optional": "bold green",
        "cx.useage.bracket": "bold yellow",

        "option": "bold green",
        "argument": "bold red",
        "group": "bold yellow",
        "description": "bold white",
    }
    
    def __init__(self,prog:str|None = None,theme:dict|None = None) -> None:
        self.root_node = _Node()
        self.prog = prog or sys.argv[0]
        self.theme = theme or self.DEFAULT_THEME

    def _compile_useage(self):

