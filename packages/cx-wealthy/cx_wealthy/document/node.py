"""通用文档节点基类。"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, Self

from rich.console import RenderableType
from rich.text import Text

__all__ = ["Node"]


class Node:
    """通用文档节点基类。

    所有节点（Group / Note / Action）的公共基类。
    提供树结构（children / parent）、层级（level）与渲染钩子。

    展示字段采用「语义字段 + 可替换渲染器」模式：

    * ``name`` / ``detail`` — 纯文本语义字段，存放节点的身份与说明文本。
    * ``titler`` / ``detailer`` — 可选的可调用渲染器，把语义字段转为 Rich 可渲染对象。
      默认为 ``_default_titler`` / ``_default_detailer``（子类可覆写注入样式）。
    * ``title`` / ``description`` — 只读计算属性，调用对应的渲染器并返回
      ``RenderableType | None``。

    ``title`` / ``description`` 的三条计算路径：

    1. 显式传 ``None`` → 返回 ``None``（「主动取消展示」）
    2. 传入非 callable → 回退调用 ``_default_titler()`` / ``_default_detailer()``
    3. 传入 callable → 完全替代默认渲染
    """

    def __init__(
        self,
        name: str | None = None,
        detail: str | None = None,
        *,
        parent: Node | None = None,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.detail = detail
        self.titler: Callable[[], RenderableType | None] | None = self._default_titler
        self.detailer: Callable[[], RenderableType | None] | None = (
            self._default_detailer
        )
        if "titler" in kwargs:
            self.titler = kwargs.pop("titler")
        if "detailer" in kwargs:
            self.detailer = kwargs.pop("detailer")
        self.parent: Node | None = None
        self._children: list[Node] = []
        if parent is not None:
            parent.add_child(self)

    @property
    def title(self) -> RenderableType | None:
        """展示标题。

        计算规则：

        1. ``self.titler is None`` → 返回 ``None``
        2. ``self.titler`` 不是 callable → 回退 ``_default_titler()``
        3. 否则 → 返回 ``self.titler()``
        """
        if self.titler is None:
            return None
        if not callable(self.titler):
            return self._default_titler()
        return self.titler()

    @property
    def description(self) -> RenderableType | None:
        """展示描述。

        计算规则：

        1. ``self.detailer is None`` → 返回 ``None``
        2. ``self.detailer`` 不是 callable → 回退 ``_default_detailer()``
        3. 否则 → 返回 ``self.detailer()``
        """
        if self.detailer is None:
            return None
        if not callable(self.detailer):
            return self._default_detailer()
        return self.detailer()

    def _default_titler(self) -> RenderableType | None:
        """默认标题渲染：纯文本 name，无样式。

        子类可覆盖此方法来定制默认样式。
        """
        if self.name is None:
            return None
        return Text(self.name)

    def _default_detailer(self) -> RenderableType | None:
        """默认描述渲染：纯文本 detail，无样式。

        子类可覆盖此方法来定制默认样式。
        """
        if self.detail is None:
            return None
        return Text(self.detail)

    def level(self) -> int:
        """节点层级，根为 0。"""
        if self.parent is None:
            return 0
        return self.parent.level() + 1

    def add_child(self, child: Node) -> Self:
        """添加子节点。安全处理从原 parent 移除。"""
        if child.parent is not None and child.parent is not self:
            try:
                child.parent._children.remove(child)
            except ValueError:
                pass
        child.parent = self
        if child not in self._children:
            self._children.append(child)
        return self

    def iter_children(self) -> Iterator[Node]:
        """迭代直接子节点。"""
        return iter(self._children)

    def walk(self) -> Iterator[Node]:
        """深度优先遍历所有后代。带 visited 集合防环。"""
        visited: set[int] = set()

        def _walk(node: Node) -> Iterator[Node]:
            for child in node.iter_children():
                child_id = id(child)
                if child_id in visited:
                    continue
                visited.add(child_id)
                yield child
                yield from _walk(child)

        return _walk(self)

    def render(self) -> RenderableType:
        """渲染本节点。默认返回 children 的 Group 或空 Text。"""
        from rich.console import Group as RichGroup

        if not self._children:
            return Text()
        return RichGroup(*(child.render() for child in self._children))

    def __rich__(self) -> RenderableType:
        return self.render()
