"""通用结构化文档顶层入口。"""

from __future__ import annotations

from collections.abc import Generator
import sys

from rich.console import Console, ConsoleOptions, RenderableType
from rich.theme import Theme

from ..theme import default_theme
from .group import Group
from .note import Note

__all__ = ["WealthyDocument"]


class WealthyDocument:
    """通用结构化文档顶层入口。

    管理 root Group 与渲染流程。帮助系统等特化层可继承此类
    并覆盖 render() 以追加专属输出。

    主题透明性
    ----------
    组件不持有主题，``style="cx.*"`` 等样式名是**约定**，由调用方通过
    ``Console(theme=...)`` 决定是否应用 :data:`cx_wealthy.default_theme`。

    渲染时**兜底补全**调用方未定义的 ``cx.*`` 样式——不覆盖调用方已有
    定义，仅在缺失时用 :data:`default_theme` 填充。这保证：

    - **cxalio tools**：``IAppEnvironment`` 设了 ``default_theme`` → 全部
      ``cx.*`` 已存在 → 不补全 → 用调用方定义
    - **第三方不设主题**：全部 ``cx.*`` 缺失 → 补全基础样式 → 组件可用
    - **第三方设自己的主题**：调用方定义优先，仅补全缺失项

    主体功能仍是 Rich 原生能力，组件对调用方主题透明兼容。
    """

    def __init__(
        self,
        *,
        prog: str | None = None,
        description: RenderableType | None = None,
        epilog: RenderableType | None = None,
    ) -> None:
        self._prog = prog
        self.description = description
        self.epilog = epilog
        self._root = Group(name="root")

    @property
    def prog(self) -> str:
        """程序名；未显式传入时延迟取 sys.argv[0]。"""
        if self._prog is None:
            return sys.argv[0]
        return self._prog

    @property
    def root(self) -> Group:
        """根 Group。"""
        return self._root

    def add_group(
        self, name: str | None = None, description: str | None = None
    ) -> Group:
        """代理到 root.add_group。"""
        return self._root.add_group(name, description)

    def add_note(
        self, *contents: RenderableType, title: RenderableType | None = None
    ) -> Note:
        """代理到 root.add_note。"""
        return self._root.add_note(*contents, title=title)

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
        """标准 Rich 渲染钩子。

        透明兼容：补全调用方未定义的 ``cx.*`` 样式，不覆盖已有定义。
        """
        # ThemeStack.get 返回 None 表示样式未定义
        ts = console._theme_stack
        missing = {
            name: value
            for name, value in default_theme.styles.items()
            if ts.get(name) is None
        }
        if missing:
            with console.use_theme(Theme(missing)):
                yield from self.render()
        else:
            yield from self.render()
