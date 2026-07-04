"""详情渲染协议与键值面板组件。"""

from __future__ import annotations

from collections.abc import Generator, Iterable, Mapping
from typing import Any

from rich.console import RenderableType
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

from .indexed_list import IndexedListPanel
from .label import RichLabel

__all__ = [
    "RichDetailMixin",
    "WealthDetailTable",
    "WealthDetailPanel",
]


class RichDetailMixin:
    """详情渲染协议 mixin。

    子类实现 __rich_detail__() 后，本 mixin 自动提供 __rich__()
    默认实现，使 console.print(obj) 直接输出 WealthDetailPanel。
    """

    def __rich_detail__(self) -> Generator[tuple[Any, ...], None, None]:
        """yield (key, value) 或 (key, value, default) 元组。

        - (key, value)：显示 key=value
        - (key, value, default)：当 value == default 时该行不显示（去重）
        - (value,)：仅显示 value，key 列为空
        - (key, *values)：value 为 list
        """
        raise NotImplementedError

    def __rich__(self) -> RenderableType:
        """默认渲染：将对象包装为 WealthDetailPanel。"""
        return WealthDetailPanel(self)


class WealthDetailTable:
    """将对象渲染为两列键值表格。

    检测优先级：__rich_detail__ > __rich_repr__ > Mapping > Iterable
    （str/bytes 显式排除，不走 Iterable 分支）
    """

    _SUB_BOX_BORDER_STYLE = "cx.detail.sub_box_border"

    def __init__(
        self,
        item: Any,
        *,
        sub_box: bool = True,
        list_max_lines: int | None = 8,
    ) -> None:
        """
        Args:
            item: 待渲染对象
            sub_box: 嵌套对象是否渲染为 sub-panel
            list_max_lines: 列表类 value 的最大行数；None 表示不限
        """
        self._item = item
        self._sub_box = sub_box
        self._list_max_lines = list_max_lines

    def make_table(self, item: Any) -> RenderableType:
        """根据对象类型生成键值表格或其他可渲染对象。"""
        if hasattr(item, "__rich_detail__"):
            return self._make_table_from_rows(self._iter_tuples(item.__rich_detail__()))
        if hasattr(item, "__rich_repr__"):
            return self._make_table_from_rows(self._iter_tuples(item.__rich_repr__()))
        if isinstance(item, Mapping):
            return self._make_table_from_rows(
                ((str(key), value) for key, value in item.items())
            )
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            return IndexedListPanel(item, max_lines=self._list_max_lines)
        return Pretty(item)

    def _make_table_from_rows(self, rows: Iterable[tuple[Any, Any]]) -> RenderableType:
        """将 (key, value) 行序列组装为 Table。"""
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cx.detail.key", ratio=1)
        table.add_column("Value", ratio=3)
        for key, value in rows:
            rendered = self._check_value(value)
            if rendered is None:
                continue
            # str → 逐字显示（数据安全）；Text → 保留已有样式；其他 → 兜底转文本
            if isinstance(key, str):
                key_text = Text(str(key))
            elif isinstance(key, Text):
                key_text = key
            else:
                key_text = Text(str(key))
            table.add_row(key_text, rendered)
        if table.row_count == 0:
            return Text("(empty)", style="cx.detail.empty")
        return table

    def _iter_tuples(
        self, generator: Generator[tuple[Any, ...], None, None]
    ) -> Generator[tuple[Any, Any], None, None]:
        """解析 __rich_detail__ / __rich_repr__ 产生的元组。"""
        for entry in generator:
            if not isinstance(entry, tuple):
                entry = (entry,)
            if len(entry) == 1:
                yield "", entry[0]
            elif len(entry) == 2:
                yield entry[0], entry[1]
            elif len(entry) == 3:
                key, value, default = entry
                if value == default:
                    continue
                yield key, value
            else:
                yield entry[0], list(entry[1:])

    def _check_value(
        self,
        value: Any,
        *,
        disable_sub_box: bool = False,
    ) -> RenderableType | None:
        """值渲染策略链。

        可扩展点：未来可抽为 ValueRenderer 策略对象，让使用方注册
        自定义类型的渲染规则。当前为内置 if-elif 链。
        """
        if value is None:
            return Text("None", style="cx.detail.none")
        if isinstance(value, (str, bytes)):
            # str/bytes 是数据，逐字显示，不解析 markup。
            # 需要 markup 格式的 value 应直接 yield Text 对象。
            return Text(str(value))
        if hasattr(value, "__rich_detail__") or hasattr(value, "__rich_repr__"):
            if self._sub_box and not disable_sub_box:
                return WealthDetailPanel(
                    value,
                    sub_box=self._sub_box,
                    list_max_lines=self._list_max_lines,
                    border_style=self._SUB_BOX_BORDER_STYLE,
                )
            return WealthDetailTable(
                value,
                sub_box=self._sub_box,
                list_max_lines=self._list_max_lines,
            ).make_table(value)
        if isinstance(value, Mapping):
            if self._sub_box and not disable_sub_box:
                return WealthDetailPanel(
                    value,
                    sub_box=self._sub_box,
                    list_max_lines=self._list_max_lines,
                    border_style=self._SUB_BOX_BORDER_STYLE,
                )
            return WealthDetailTable(
                value,
                sub_box=self._sub_box,
                list_max_lines=self._list_max_lines,
            ).make_table(value)
        if isinstance(value, (list, tuple)):
            rendered_items = [self._check_value(v, disable_sub_box=True) for v in value]
            return IndexedListPanel(rendered_items, max_lines=self._list_max_lines)
        if hasattr(value, "__rich_label__"):
            return RichLabel(value).__rich__()
        try:
            return Pretty(value)
        except Exception:  # pragma: no cover - defensive fallback
            return Text(str(value))


class WealthDetailPanel:
    """详情面板：将对象渲染为带标题/副标题的 Panel 包裹的 WealthDetailTable。"""

    def __init__(
        self,
        item: Any,
        *,
        title: str | None = None,
        border_style: str | None = None,
        sub_box: bool = True,
        list_max_lines: int | None = 8,
    ) -> None:
        """
        Args:
            item: 待渲染对象
            title: 面板标题；None 时使用 item 的类名
            border_style: 边框样式；None 时 "none"
            sub_box: 嵌套对象是否渲染为 sub-panel
            list_max_lines: 列表类 value 最大行数；None 不限
        """
        self._item = item
        self._title = title
        self._border_style = border_style
        self._sub_box = sub_box
        self._list_max_lines = list_max_lines

    def __rich__(self) -> RenderableType:
        """渲染为 Panel 包裹的 WealthDetailTable。"""
        table = WealthDetailTable(
            self._item,
            sub_box=self._sub_box,
            list_max_lines=self._list_max_lines,
        ).make_table(self._item)

        class_name = (
            None if isinstance(self._item, Mapping) else type(self._item).__name__
        )
        title = self._title if self._title is not None else class_name
        subtitle = class_name if self._title is not None and class_name else None

        return Panel(
            table,
            title=title,
            subtitle=subtitle,
            border_style=self._border_style or "none",
        )
