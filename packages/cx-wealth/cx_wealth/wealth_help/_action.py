import re
from typing import Literal, override

from ._node import _Node
from .. import rich_types as r


_ActionNargs = Literal["?", "+", "*", "**"]


class _Action(_Node):

    def __init__(
        self,
        *flags,
        name: str | None = None,
        description: str | None = None,
        metavar: str | None = None,
        nargs: int | _ActionNargs | None = None,
        optional: bool | None = None,
        parent: _Node | None = None,
    ) -> None:
        super().__init__(name=name, description=description, parent=parent)
        self.flags = [str(x) for x in flags]
        self.metavar = metavar
        self.nargs = nargs
        self.optional = optional

    def _argument(self):
        return (
            self.metavar
            or (self.flags[0] if self.flags and self.is_positional() else None)
            or self.name
            or ""
        )

    def _format_argument(self, pattern: str | None = None) -> r.Text:
        a = self._argument() if pattern is None else pattern.format(self._argument())
        return r.Text(a, style="cx.help.usage.argument")

    def is_positional(self) -> bool:
        return not self.flags or all(not re.match(r"^[-+]+\w+", x) for x in self.flags)

    def is_optional(self) -> bool:
        if self.optional is not None:
            return self.optional

        return not self.is_positional() or self.nargs == "?"

    @staticmethod
    def _format_option(option: str) -> r.Text:
        return r.Text(option, style="cx.help.usage.option")

    @staticmethod
    def _make_optional(*text: r.Text | str | None) -> r.Text:
        left = ("[", "cx.help.usage.bracket")
        right = ("]", "cx.help.usage.bracket")
        ts = [
            x if isinstance(x, r.Text) else r.Text.from_markup(x)
            for x in text
            if x is not None
        ]
        return r.Text.assemble(left, *ts, right)

    def render_options(self, sep: str = "|") -> r.Text | None:
        if not self.flags:
            return None

        elements = [self._format_option(x) for x in self.flags]
        separator = r.Text(sep, style="cx.help.usage.bracket")
        return separator.join(elements)

    def render_argument(self) -> r.Text | None:
        if not self._argument():
            return None

        if isinstance(self.nargs, int):
            args = [
                self._format_argument(pattern="{}" + str(i + 1))
                for i in range(self.nargs)
            ]
            sep = r.Text(", ", style="cx.help.usage.bracket")
            return sep.join(args)

        sep = r.Text(", ", style="cx.help.usage.bracket")

        if self.nargs == "+":
            args = [
                self._format_argument(pattern="{}1"),
                self._make_optional(sep, self._format_argument(pattern="{}2")),
                self._make_optional(sep, self._format_argument(pattern="{}3")),
                self._make_optional(sep, self._format_argument(pattern="{}...")),
            ]
            return r.Text.assemble(*args)

        if self.nargs == "*":
            args = [
                self._make_optional(self._format_argument(pattern="{}1")),
                self._make_optional(sep, self._format_argument(pattern="{}2")),
                self._make_optional(sep, self._format_argument(pattern="{}3")),
                self._make_optional(sep, self._format_argument(pattern="{}...")),
            ]
            return r.Text.assemble(*args)

        return self._format_argument()

    @override
    def render_usage(self) -> r.Text:
        res = r.Text()
        if self.is_positional():
            res = self.render_argument() or res
        else:
            ps = [self.render_options(), self.render_argument()]
            res = r.Text(" ").join([x for x in ps if x is not None])

        if self.nargs == "**":
            res = r.Text.assemble(
                self._make_optional(res),
                self._make_optional(
                    self.render_options(),
                    r.Text(" ...", style="cx.help.usage.argument"),
                ),
            )

        if self.is_optional():
            res = self._make_optional(res)

        return res

    def render_detail_title(self):
        res = r.Text()
        if self.is_positional():
            res = self.render_argument() or res
        else:
            ps = [self.render_options(","), self.render_argument()]
            res = r.Text(" ").join([x for x in ps if x is not None])
        return res

    @override
    @r.group(True)
    def render_details(self):
        yield self.render_detail_title()
        if self.description:
            yield r.Padding(
                r.Text.from_markup(
                    self.description, style="cx.help.details.description"
                ),
                pad=(0, 0, 0, 4),
            )
