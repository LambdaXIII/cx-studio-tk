"""帮助特化节点：Action。"""

from __future__ import annotations

import re
from typing import Literal

from rich.console import RenderableType
from rich.text import Text

from ..document.node import Node

__all__ = ["Action"]


class Action(Node):
    """帮助特化节点：表示一个命令行选项 / 位置参数。

    继承通用 :class:`Node`，增加 flags、nargs、metavar 等 help 特化概念。
    """

    def __init__(
        self,
        *flags: str,
        name: str | None = None,
        description: str | None = None,
        metavar: str | None = None,
        nargs: int | Literal["?", "+", "*", "**"] | None = None,
        optional: bool | None = None,
        parent: Node | None = None,
        prefix_chars: str = "-",
    ) -> None:
        """
        Args:
            flags: 选项标志（如 ``-h``、``--help``）；空表示位置参数。
            name: 参数名（用于详情展示）。
            description: 参数说明。
            metavar: 占位符（如 FILE、DIR）。
            nargs: 参数数量；整数或 ``?``(0或1) / ``+``(1+) / ``*``(0+) / ``**``(可重复)。
            optional: 是否可选；None 时自动推断。
            parent: 父节点。
            prefix_chars: 标识可选参数的前缀字符集合，默认为 ``-``。
        """
        self.flags = tuple(flags)
        self.metavar = metavar
        self.nargs = nargs
        self.optional = optional
        self.prefix_chars = prefix_chars
        self._validate_flags()
        super().__init__(name=name, description=description, parent=parent)

    def _validate_flags(self) -> None:
        r"""校验每个 flag 格式。

        非空 flag 必须以 ``prefix_chars`` 中的字符开头，并且整体符合
        ``^[prefix_chars]+\w+``；拦截 ``--jobs--max-workers``、``foo bar`` 等错误。
        """
        escaped = re.escape(self.prefix_chars)
        pattern = re.compile(rf"^[{escaped}]+\w+$")
        for flag in self.flags:
            if not flag:
                continue
            if flag[0] not in self.prefix_chars or not pattern.match(flag):
                raise ValueError(f"Invalid flag: {flag!r}")

    def is_positional(self) -> bool:
        """是否为位置参数。

        当 flags 为空，或所有 flag 都不以 ``prefix_chars`` 开头时返回 True。
        """
        if not self.flags:
            return True
        return all(not flag or flag[0] not in self.prefix_chars for flag in self.flags)

    def is_optional(self) -> bool:
        """是否为可选参数。

        若构造时显式传入 ``optional`` 则使用显式值，否则按 ``is_positional`` 推断。
        位置参数若 nargs 为 ``"?"`` 也视为可选。
        """
        if self.optional is not None:
            return self.optional
        return not self.is_positional() or self.nargs == "?"

    def _format_argument(self, metavar: str, index: int) -> str:
        """生成带索引的参数占位符字符串，使用 f-string 避免 ``{`` 被误解析。"""
        return f"{metavar}{index + 1}"

    def _make_optional(self, text: Text) -> Text:
        """用方括号包裹文本，表示可选。"""
        result = Text()
        result.append("[", style="cx.help.usage.bracket")
        result.append_text(text)
        result.append("]", style="cx.help.usage.bracket")
        return result

    def _format_option(self, flag: str) -> Text:
        """格式化 flag 文本。"""
        return Text(flag, style="cx.help.usage.option")

    def _usage_argument_text(self) -> Text | None:
        """生成 usage 中的参数占位符部分。

        注：nargs="**" 的渲染逻辑在 render_usage() 中专门处理，不在此处。
        """
        if self.is_optional() and self.metavar is None and self.nargs is None:
            return None

        metavar = self.metavar or self.name or ("VAL" if self.is_optional() else "ARG")
        style = "cx.help.usage.argument"
        sep_style = "cx.help.usage.bracket"

        if isinstance(self.nargs, int):
            count = max(0, self.nargs)
            if count == 0:
                return None
            parts = [
                Text(self._format_argument(metavar, i), style=style)
                for i in range(count)
            ]
            result = Text()
            for i, part in enumerate(parts):
                if i:
                    result.append(", ", style=sep_style)
                result.append_text(part)
            return result

        if self.nargs == "+":
            result = Text()
            result.append(self._format_argument(metavar, 0), style=style)
            for i in range(1, 3):
                part = Text()
                part.append(", ", style=sep_style)
                part.append(self._format_argument(metavar, i), style=style)
                result.append_text(self._make_optional(part))
            more = Text()
            more.append(", ", style=sep_style)
            more.append(f"{metavar}...", style=style)
            result.append_text(self._make_optional(more))
            return result

        if self.nargs == "*":
            result = self._make_optional(
                Text(self._format_argument(metavar, 0), style=style)
            )
            for i in range(1, 3):
                part = Text()
                part.append(", ", style=sep_style)
                part.append(self._format_argument(metavar, i), style=style)
                result.append_text(self._make_optional(part))
            more = Text()
            more.append(", ", style=sep_style)
            more.append(f"{metavar}...", style=style)
            result.append_text(self._make_optional(more))
            return result

        if self.nargs == "?":
            return Text(self._format_argument(metavar, 0), style=style)

        return Text(metavar, style=style)

    def _build_flags_text(self) -> Text:
        """构建 flags 文本（用 | 分隔多个 flag）。"""
        result = Text()
        for i, flag in enumerate(self.flags):
            if i:
                result.append("|", style="cx.help.usage.bracket")
            result.append_text(self._format_option(flag))
        return result

    def render_usage(self) -> Text:
        """渲染 usage 行片段。"""
        usage = Text()
        arg_text = self._usage_argument_text()

        if self.nargs == "**" and not self.is_positional():
            flags_text = self._build_flags_text()
            metavar = self.metavar or self.name or "VAL"
            base = Text()
            base.append_text(flags_text)
            base.append(" ")
            base.append(metavar, style="cx.help.usage.argument")
            repeat = Text()
            repeat.append_text(flags_text)
            repeat.append(" ...")
            usage.append_text(self._make_optional(base))
            usage.append(" ")
            usage.append_text(self._make_optional(repeat))
            return usage

        if self.is_optional():
            inner = Text()
            inner.append_text(self._build_flags_text())
            if arg_text is not None:
                inner.append(" ")
                inner.append_text(arg_text)
            usage.append_text(self._make_optional(inner))
        else:
            if arg_text is not None:
                usage.append_text(arg_text)
            else:
                usage.append(self.name or "ARG", style="cx.help.usage.argument")

        return usage

    def render_details(self) -> RenderableType:
        """渲染详情条目（flags + metavar + description）。"""
        line = Text()
        flags_text = (
            ", ".join(self.flags)
            if self.flags
            else (self.metavar or self.name or "ARG")
        )
        line.append(flags_text, style="cx.help.usage.option")
        if self.metavar:
            line.append(f"  {self.metavar}", style="cx.help.usage.argument")
        if self.description:
            line.append(f"  {self.description}", style="cx.help.details.description")
        return line
