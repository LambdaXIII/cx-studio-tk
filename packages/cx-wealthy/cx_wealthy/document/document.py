"""通用结构化文档顶层入口。"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from rich.console import Console, ConsoleOptions, RenderableType

from .group import Group
from .note import Note

__all__ = ["WealthyDocument"]


class WealthyDocument:
    """通用结构化文档顶层入口。

    管理 root Group 与渲染流程。帮助系统等特化层可继承此类
    并覆盖 render() 以追加专属输出。

    主题透明性
    ----------
    组件不持有主题，也不在渲染时导入或补全任何主题。``style="cx.*"``
    等样式名是**约定**，由调用方通过 ``Console(theme=...)`` 决定样式值。
    不设主题时 ``cx.*`` 样式静默不生效（Rich 默认行为），内容仍完整可读。
    """

    def __init__(
        self,
        *,
        description: RenderableType | None = None,
        epilog: RenderableType | None = None,
    ) -> None:
        self.description = description
        self.epilog = epilog
        self._root = Group(name="root")

    @property
    def root(self) -> Group:
        """根 Group。"""
        return self._root

    def add_group(
        self,
        name: str | None = None,
        detail: str | None = None,
        **kwargs: Any,
    ) -> Group:
        """代理到 root.add_group。

        ``**kwargs`` 可接收 ``titler`` / ``detailer``，透传给底层。
        """
        return self._root.add_group(name=name, detail=detail, **kwargs)

    def add_note(
        self,
        *contents: RenderableType,
        title: RenderableType | None = None,
        **kwargs: Any,
    ) -> Note:
        """代理到 root.add_note。

        ``**kwargs`` 可接收 ``titler`` / ``detailer``，透传给 Note。
        """
        return self._root.add_note(*contents, title=title, **kwargs)

    def render(self) -> Generator[RenderableType, None, None]:
        """yield 文档各部分。"""
        if self.description is not None:
            yield self.description

        # root 是隐藏容器，不渲染其自身 name，仅暴露子节点。
        for child in self._root.iter_children():
            yield child.render()

        if self.epilog is not None:
            yield self.epilog

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> Generator[RenderableType, None, None]:
        """标准 Rich 渲染钩子。"""
        yield from self.render()
