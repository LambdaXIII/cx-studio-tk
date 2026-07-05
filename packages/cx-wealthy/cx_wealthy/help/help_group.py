"""帮助特化容器：兼具参数分组与子命令两种语义角色。"""

from __future__ import annotations

from collections.abc import Generator
from typing import Literal, override

from rich.console import RenderableType
from rich.text import Text

from ..document.group import Group
from ..document.node import Node
from .action import Action

__all__ = ["HelpGroup"]


class HelpGroup(Group):
    """帮助特化容器：兼具参数分组与子命令两种语义角色。

    通过 commands 字段区分：
    - commands=() → 参数分组（旧 ActionGroup 语义），自己不是命令
    - commands=("list",) → 命令本身（旧 CommandGroup 语义），参与 usage pipe 列表

    既有容器能力（继承 Group 的 add_group/add_note），
    也有 add_action（添加专有参数）和 add_command（添加子命令）。
    """

    def __init__(
        self,
        *commands: str,
        name: str | None = None,
        detail: str | None = None,
        parent: Node | None = None,
        **kwargs: object,
    ) -> None:
        """初始化 HelpGroup。

        Args:
            *commands: 命令关键词。空表示容器，非空表示命令本身。
            name: 节点名称。
            detail: 描述文本。
            parent: 父节点。
            **kwargs: 可接收 ``titler`` / ``detailer``，透传给 Node。
        """
        self.commands = tuple(commands)
        super().__init__(name=name, detail=detail, parent=parent, **kwargs)

    @property
    def is_command(self) -> bool:
        """是否为命令本身（commands 非空），而非纯参数分组。"""
        return bool(self.commands)

    @override
    def _default_titler(self) -> RenderableType | None:
        if self.name is None:
            return None
        return Text(self.name, style="cx.help.group.title")

    @override
    def _default_detailer(self) -> RenderableType | None:
        if self.detail is None:
            return None
        return Text(self.detail, style="cx.help.group.description")

    def add_action(
        self,
        *flags: str,
        name: str | None = None,
        detail: str | None = None,
        metavar: str | None = None,
        nargs: int | Literal["?", "+", "*", "**"] | None = None,
        optional: bool | None = None,
        prefix_chars: str = "-",
    ) -> Action:
        """添加 Action 子节点并返回。"""
        return Action(
            *flags,
            name=name,
            detail=detail,
            metavar=metavar,
            nargs=nargs,
            optional=optional,
            parent=self,
            prefix_chars=prefix_chars,
        )

    def add_command(
        self,
        *keywords: str,
        name: str | None = None,
        detail: str | None = None,
        **kwargs: object,
    ) -> "HelpGroup":
        """添加子命令并返回，支持链式构建。

        ``**kwargs`` 可接收 ``titler`` / ``detailer``。
        """
        return HelpGroup(*keywords, name=name, detail=detail, parent=self, **kwargs)

    def iter_commands(self) -> Generator["HelpGroup", None, None]:
        """递归穿透非命令 HelpGroup，收集所有 is_command=True 的子孙。

        用于 usage 渲染：非命令容器（commands=()，如"子命令"分组）的
        命令子节点需要 bubble up 到其父节点的 sub_commands 列表。
        嵌套非命令容器（如"基本命令"/"高级命令"）递归展开。
        """
        for child in self.iter_children():
            if isinstance(child, HelpGroup):
                if child.is_command:
                    yield child
                else:
                    yield from child.iter_commands()
