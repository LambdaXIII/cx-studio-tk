"""帮助系统特化文档：WealthyHelp。"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Generator
from typing import Literal, override

from rich.align import Align
from rich.console import Group as RichGroup, RenderableType
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..theme import BASE_STYLES, HELP_STYLES
from ..document.document import WealthyDocument
from ..document.note import Note
from .action import Action

__all__ = ["WealthyHelp"]


class WealthyHelp(WealthyDocument):
    """帮助系统特化文档。

    继承 :class:`WealthyDocument` 的通用文档能力，增加 ``add_action()``、
    ``render_usage()``、``render_details()``、``render_epilog()``。
    """

    DEFAULT_STYLES: dict[str, str] = {**BASE_STYLES, **HELP_STYLES}

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
        for key in ("optional", "positional", "other"):
            for fragment in buckets[key]:
                usage.append(" ")
                usage.append_text(fragment)

        table = Table(box=None, show_header=False, padding=(0, 0))
        table.add_column(style="cx.help.usage.prog", justify="left", no_wrap=True)
        table.add_column(ratio=1)
        table.add_row(Text(self.prog, style="cx.help.usage.prog"), usage)

        parts: list[RenderableType] = [table]

        if self.description is not None:
            if isinstance(self.description, str):
                desc_renderable = Text.from_markup(self.description)
            else:
                desc_renderable = self.description
            parts.append(Padding(desc_renderable, pad=(1, 0, 0, 2)))

        content = RichGroup(*parts) if len(parts) > 1 else parts[0]

        return Panel(
            content,
            title=Text("用法", style="cx.help.usage.title"),
            border_style="cx.help.details.box",
        )

    def render_details(self) -> RenderableType:
        """渲染参数详情，按 Group 分组。"""
        from ..document.group import Group

        all_actions = [node for node in self.root.walk() if isinstance(node, Action)]
        if not all_actions:
            return Text("")

        parts: list[RenderableType] = []

        ungrouped_actions: list[Action] = []
        for child in self.root.iter_children():
            if isinstance(child, Action):
                ungrouped_actions.append(child)

        for action in ungrouped_actions:
            parts.append(action.render_details())

        for child in self.root.iter_children():
            if isinstance(child, Group):
                group_parts: list[RenderableType] = []

                if child.name:
                    title_text = Text(child.name, style="cx.help.group.title")
                    title_text.stylize("bold")
                    group_parts.append(title_text)

                if child.description:
                    group_parts.append(
                        Padding(
                            Text(child.description, style="cx.help.group.description"),
                            pad=(0, 0, 0, 2),
                        )
                    )

                group_actions: list[Action] = []
                for group_child in child.iter_children():
                    if isinstance(group_child, Action):
                        group_actions.append(group_child)

                if group_actions:
                    action_lines = [a.render_details() for a in group_actions]
                    group_parts.append(
                        Padding(RichGroup(*action_lines), pad=(0, 0, 0, 4))
                    )

                if group_parts:
                    if parts:
                        parts.append(Text(""))
                    parts.append(RichGroup(*group_parts))

        content = RichGroup(*parts) if len(parts) > 1 else parts[0]

        return Panel(
            content,
            title="参数详情",
            border_style="cx.help.details.box",
        )

    def render_epilog(self) -> RenderableType | None:
        """渲染尾部内容或 notes；为空时返回 None。"""
        parts: list[RenderableType] = []

        if self.epilog is not None:
            if isinstance(self.epilog, str):
                epilog_text = Text.from_markup(self.epilog, style="cx.help.epilog")
                parts.append(Align.right(epilog_text))
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
