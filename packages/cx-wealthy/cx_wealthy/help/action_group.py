"""帮助特化的 Group：提供 add_action 便利方法。

设计意图：:class:`~cx_wealthy.document.group.Group` 是 ``document`` 通用核心，
不应感知 ``help`` 特化层的 :class:`Action`。但调用方在构建帮助时希望直接
``group.add_action(...)`` 而非 ``group.add_child(Action(...))``。

本类在 ``help`` 特化层继承 :class:`Group`，补充 ``add_action`` 便利方法——
由 :class:`WealthyHelp.add_group` 返回，使调用方获得便利的同时不污染通用核心。
"""

from __future__ import annotations

from typing import Literal

from ..document.group import Group
from .action import Action

__all__ = ["ActionGroup"]


class ActionGroup(Group):
    """帮助特化 Group：在 Group 基础上提供 :meth:`add_action` 便利方法。

    与 :class:`WealthyHelp` 配合使用——``WealthyHelp.add_group`` 返回
    :class:`ActionGroup`，使调用方可直接 ``group.add_action(...)`` 构建帮助结构。

    若需在通用文档场景使用 Group，应直接用 :class:`Group` 而非本类。
    """

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
        """添加 :class:`Action` 子节点并返回。"""
        return Action(
            *flags,
            name=name,
            description=description,
            metavar=metavar,
            nargs=nargs,
            optional=optional,
            parent=self,
            prefix_chars=prefix_chars,
        )
