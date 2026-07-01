"""帮助系统特化文档：WealthyHelp。"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Generator
from typing import Literal, override

from rich import box
from rich.console import Group as RichGroup, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..document.document import WealthyDocument
from ..document.note import Note
from .action import Action

__all__ = ["WealthyHelp"]


class WealthyHelp(WealthyDocument):
    """帮助系统特化文档。

    继承 :class:`WealthyDocument` 的通用文档能力，增加 ``add_action()``、
    ``render_usage()``、``render_details()``、``render_epilog()``。
    """

    HELP_STYLES: dict[str, str] = {
        **WealthyDocument.DEFAULT_STYLES,
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
    DEFAULT_STYLES = HELP_STYLES

    def __init__(
        self,
        *,
        prog: str | None = None,
        description: RenderableType | None = None,
        epilog: RenderableType | None = None,
        styles: dict[str, str] | None = None,
    ) -> None:
        """
        Args:
            prog: 程序名；None 时在 render 阶段延迟取 ``sys.argv[0]``。
            description: 文档描述。
            epilog: 尾部内容。
            styles: 样式覆盖（合并到默认样式的拷贝，不污染类属性）。
        """
        super().__init__(
            prog=prog, description=description, epilog=epilog, styles=styles
        )

    def add_action(
        self,
        *flags: str,
        name: str | None = None,
        description: str | None = None,
        metavar: str | None = None,
        nargs: int | Literal["?", "+", "*", "**"] | None = None,
        optional: bool | None = None,
        prefix_chars: str = "-",
    ) -> Action:
        """创建 :class:`Action` 并添加到 root，返回该 ``Action``。"""
        return Action(
            *flags,
            name=name,
            description=description,
            metavar=metavar,
            nargs=nargs,
            optional=optional,
            parent=self.root,
            prefix_chars=prefix_chars,
        )

    @override
    def render(self) -> Generator[RenderableType, None, None]:
        """yield usage、details、epilog（非空）。"""
        yield self.render_usage()
        yield self.render_details()
        epilog = self.render_epilog()
        if epilog is not None:
            yield epilog

    def render_usage(self) -> RenderableType:
        """渲染用法行。

        使用 ``defaultdict(list)`` 按 ``(is_optional, is_positional)`` 累积，
        再按固定顺序重组，避免 ``itertools.groupby`` 的连续 key 依赖问题。
        """
        actions = [node for node in self.root.walk() if isinstance(node, Action)]
        buckets: dict[str, list[Text]] = defaultdict(list)

        for action in actions:
            if action.is_optional() and not action.is_positional():
                buckets["optional"].append(action.render_usage())
            elif action.is_positional():
                buckets["positional"].append(action.render_usage())
            else:
                buckets["other"].append(action.render_usage())

        usage = Text()
        usage.append("用法：", style="cx.help.usage.title")
        usage.append(self.prog, style="cx.help.usage.prog")

        for key in ("optional", "positional", "other"):
            for fragment in buckets[key]:
                usage.append(" ")
                usage.append_text(fragment)

        return usage

    def render_details(self) -> RenderableType:
        """渲染参数详情表格。"""
        actions = [node for node in self.root.walk() if isinstance(node, Action)]
        if not actions:
            return Text("")

        table = Table(
            show_header=True,
            box=box.SIMPLE_HEAD,
            border_style="cx.help.details.box",
        )
        table.add_column("参数", style="cx.help.usage.option")
        table.add_column("占位符", style="cx.help.usage.argument")
        table.add_column("说明", style="cx.help.details.description")

        for action in actions:
            flags = ", ".join(action.flags) if action.flags else ""
            table.add_row(
                flags,
                action.metavar or "",
                action.description or "",
            )

        return Panel(
            table,
            title="参数详情",
            border_style="cx.help.details.box",
        )

    def render_epilog(self) -> RenderableType | None:
        """渲染尾部内容或 notes；为空时返回 None。"""
        parts: list[RenderableType] = []

        if self.epilog is not None:
            if isinstance(self.epilog, str):
                parts.append(Text(self.epilog, style="cx.help.epilog"))
            else:
                parts.append(self.epilog)

        for node in self.root.walk():
            if isinstance(node, Note):
                parts.append(node.render())

        if not parts:
            return None
        if len(parts) == 1:
            return parts[0]
        return RichGroup(*parts)
