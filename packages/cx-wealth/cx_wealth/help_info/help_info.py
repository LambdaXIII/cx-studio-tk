import itertools
from tokenize import tabsize
from ._node import _Node
from ._action import _Action
from ._group import _Group
from .. import _rich as r
import sys, re
from typing import Literal


class WealthHelpInfomation:
    DEFAULT_STYLES = {
        "cx.help.useage.title": "green",
        "cx.help.useage.prog": "orange1",
        "cx.help.useage.bracket": "bright_black",
        "cx.help.useage.option": "cyan",
        "cx.help.useage.argument": "italic yellow",
        "cx.help.group.title": "orange1",
        "cx.help.group.description": "italic dim default",
        "cx.help.details.box": "blue",
        "cx.help.details.description": "italic default",
    }

    def __init__(
        self,
        prog: str | None = None,
        description: str | None = None,
        styles: dict | None = None,
    ):
        self.prog = prog or sys.argv[0]
        self.description = description
        self._root = _Group(prog, description)
        self.styles = self.DEFAULT_STYLES
        if styles is not None:
            self.styles.update(styles)
        self.theme = r.Theme(self.styles)

    def add_action(
        self,
        *flags,
        name: str | None = None,
        description: str | None = None,
        metavar: str | None = None,
        nargs: int | Literal["?", "+", "*"] | None = None,
        optional: bool | None = None,
    ) -> _Action:
        return self._root.add_action(
            *flags,
            name=name,
            description=description,
            metavar=metavar,
            nargs=nargs,
            optional=optional,
        )

    def add_group(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> _Group:
        return self._root.add_group(name=name, description=description)

    def render_useage(self) -> r.RenderableType:
        def separate(x: _Action):
            a = "o" if x.is_optional() else ""
            b = "+p" if x.is_positional() else "-p"
            return a + b

        grouped_actions = {
            k: list(v)
            for k, v in itertools.groupby(self._root.iter_actions(), key=separate)
        }

        useages = [
            x.render_useage()
            for x in itertools.chain(
                *(grouped_actions.get(x, []) for x in ["o-p", "-p", "o+p", "+p"])
            )
        ]
        useage = r.Text(" ").join(useages)

        program = r.Text(self.prog, style="cx.help.useage.prog")
        table = r.Table(box=None, show_header=False, expand=True)
        table.add_column("prog", no_wrap=True, overflow="ignore")
        table.add_column("useage", overflow="fold")
        table.add_row(program, useage)
        return r.Panel(
            table,
            title="用法",
            expand=True,
            title_align="left",
            style="cx.help.useage.title",
        )

    def render_details(self) -> r.RenderableType:
        details = [x.render_details() for x in self._root.children]
        return r.Panel(
            r.Group(*details),
            title="参数详情",
            expand=True,
            title_align="left",
            style="cx.help.details.box",
        )

    @r.group(True)
    def render(self):
        yield self.render_useage()
        yield self.render_details()

    def __rich_console__(self, console: r.Console, options: r.ConsoleOptions):
        with console.use_theme(self.theme):
            o = options.update(highlight=False)
            yield from console.render(self.render(), o)
