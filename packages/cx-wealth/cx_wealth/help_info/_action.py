from ._node import _Node
from typing import Literal, override
from .. import _rich as r
import re


class _Action(_Node):

    def __init__(
        self,
        *flags,
        name: str | None = None,
        description: str | None = None,
        metavar: str | None = None,
        nargs: int | Literal["?", "+", "*"] | None = None,
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
        return r.Text(a, style="cx.help.useage.argument")

    def is_positional(self) -> bool:
        return not self.flags or all(not re.match(r"^[-+]+\w+", x) for x in self.flags)

    def is_optional(self) -> bool:
        if self.optional is not None:
            return self.optional

        return not self.is_positional() or self.nargs == "?"

    @staticmethod
    def _format_option(option: str) -> r.Text:
        return r.Text(option, style="cx.help.useage.option")

    @staticmethod
    def _make_optional(*text: r.Text | str | None) -> r.Text:
        left = ("[", "cx.help.useage.bracket")
        right = ("]", "cx.help.useage.bracket")
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
        separator = r.Text(sep, style="cx.help.useage.bracket")
        return separator.join(elements)

    def render_argument(self) -> r.Text | None:
        if not self._argument():
            return None

        if isinstance(self.nargs, int):
            args = [
                self._format_argument(pattern=f"{"{}"}{i+1}") for i in range(self.nargs)
            ]
            sep = r.Text(", ", style="cx.help.useage.bracket")
            return sep.join(args)

        sep = r.Text(", ", style="cx.help.useage.bracket")

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
    def render_useage(self) -> r.Text:
        res = r.Text()
        if self.is_positional():
            res = self.render_argument() or res
        else:
            ps = [self.render_options(), self.render_argument()]
            res = r.Text(" ").join([x for x in ps if x is not None])

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
            yield r.Text("\t") + r.Text.from_markup(
                self.description, style="cx.help.details.description"
            )
