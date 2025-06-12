import itertools
import sys
from collections.abc import Iterable

from ._action import _Action, _ActionNargs
from ._group import _Group
from .. import rich_types as r


class WealthHelp:
    DEFAULT_STYLES = {
        "cx.help.usage.title": "green",
        "cx.help.usage.prog": "orange1",
        "cx.help.usage.bracket": "bright_black",
        "cx.help.usage.option": "cyan",
        "cx.help.usage.argument": "italic yellow",
        "cx.help.group.title": "orange1",
        "cx.help.group.description": "italic dim default",
        "cx.help.details.box": "blue",
        "cx.help.details.description": "italic default",
        "cx.help.epilog": "dim italic default",
    }

    def __init__(
        self,
        prog: str | None = None,
        description: str | r.RenderableType | None = None,
        epilog: str | r.RenderableType | None = None,
        styles: dict | None = None,
    ):
        self.prog = prog or sys.argv[0]
        self.description = description
        self._root = _Group()
        self.styles = self.DEFAULT_STYLES
        self.epilog = epilog
        if styles is not None:
            self.styles.update(styles)
        self.theme = r.Theme(self.styles)

    def add_action(
        self,
        *flags,
        name: str | None = None,
        description: str | None = None,
        metavar: str | None = None,
        nargs: int | _ActionNargs | None = None,
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

    def render_description(self) -> r.RenderableType | None:
        if isinstance(self.description, str):
            desc = r.Text.from_markup(
                self.description, style="cx.help.group.description"
            )
            # desc.no_wrap = True
            desc.overflow = "fold"
        elif isinstance(self.description, r.RenderableType):
            desc = self.description
        else:
            return None

        return (
            r.Padding(
                desc,
                (1, 1, 0, 1),
            )
            if self.description
            else None
        )

    def render_epilog(self) -> r.RenderableType | None:
        if isinstance(self.epilog, str):
            return r.Text.from_markup(
                self.epilog, style="cx.help.epilog", justify="right"
            )
        if isinstance(self.epilog, r.RenderableType):
            return self.epilog
        return None

    def render_usage(self) -> r.RenderableType:
        def separate(x: _Action):
            a = "o" if x.is_optional() else ""
            b = "+p" if x.is_positional() else "-p"
            return a + b

        grouped_actions = {
            k: list(v)
            for k, v in itertools.groupby(self._root.iter_actions(), key=separate)
        }

        usages = [
            x.render_usage()
            for x in itertools.chain(
                *(grouped_actions.get(x, []) for x in ["o-p", "-p", "o+p", "+p"])
            )
        ]
        usage = r.Text(" ").join(usages)

        program = r.Text(self.prog, style="cx.help.usage.prog")
        table = r.Table(box=None, show_header=False, expand=True)
        table.add_column("prog", no_wrap=True, overflow="ignore")
        table.add_column("usage", overflow="fold")
        table.add_row(program, usage)

        desc = self.render_description()

        return r.Panel(
            r.Group(table, desc) if desc else table,
            title="用法",
            expand=True,
            title_align="left",
            style="cx.help.usage.title",
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

    def render(self) -> Iterable[r.RenderableType]:
        yield self.render_usage()
        yield self.render_details()
        r_epilog = self.render_epilog()
        if r_epilog:
            yield r_epilog

    def __rich_console__(self, console: r.Console, options: r.ConsoleOptions):
        with console.use_theme(self.theme):
            o = options.update(highlight=False)
            yield from console.render(r.Group(*self.render(), fit=True), o)
