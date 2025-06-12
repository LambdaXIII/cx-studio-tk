from collections.abc import Sequence, Iterable

from . import rich_types as r


class IndexedListPanel:
    """索引列表面板，用于在终端中以带索引的表格形式显示列表内容。

    功能特点：
    - 索引编号右对齐并绿色高亮显示
    - 支持设置起始索引（默认1）
    - 提供最大显示行数控制，超过时显示省略提示
    - 自动计算索引宽度适配最大值位数
    - 自带面板封装，显示项数统计信息
    - 支持边框样式定制（使用Rich样式语法）

    该组件基于Rich库的Table和Panel组件实现，适用于命令行工具的列表展示场景。
    """

    def __init__(
        self,
        items: Sequence | Iterable,
        title: str | None = None,
        start_index: int = 1,
        max_lines: int = 20,
        border_style: r.StyleType | None = None,
    ):
        """初始化索引列表面板

        Args:
            items (Sequence | Iterable): 待展示的列表数据源
            title (str, optional): 面板标题. Defaults to None.
            start_index (int, optional): 索引起始值，默认从1开始. Defaults to 1.
            max_lines (int, optional): 最大显示行数，超过时截断并提示剩余项数. Defaults to 20.
            border_style (rich.StyleType, optional): 边框样式，支持Rich样式名称或对象. Defaults to "none".
        """
        self._items = list(items)
        self._title = title
        self._start_index = start_index
        self._max_lines = max_lines
        self._border_style = border_style or "none"

    @staticmethod
    def default_width_calculator(console: r.Console) -> int:
        """计算默认表格宽度（占终端宽度的80%）

        Args:
            console (rich.Console): 当前控制台实例

        Returns:
            int: 计算后的宽度值
        """
        return int(console.width * 0.8)

    @staticmethod
    def __check_item(item) -> r.RenderableType:
        """验证并适配项的渲染格式

        Args:
            item (Any): 待检查的项内容

        Returns:
            rich.RenderableType: 可渲染对象（不可渲染时转为字符串）
        """
        if r.protocol.is_renderable(item):
            return item
        return str(item)

    def get_table(self) -> r.Table:
        """生成带索引的表格对象

        Returns:
            rich.Table: 包含索引列和内容列的表格对象
        """
        table = r.Table(show_header=False, box=None)
        table.add_column("index", justify="right", style="green", ratio=1)
        table.add_column(
            "content",
            justify="left",
            highlight=True,
            overflow="fold",
            ratio=200,
        )

        total = len(self._items)
        total_digits = len(str(total))

        if self._max_lines <= 0 or self._max_lines + 1 >= total:
            for i, item in enumerate(self._items, start=self._start_index):
                table.add_row(f"{i:>{total_digits}}", self.__check_item(item))

        else:
            safe_lines = self._max_lines - 2
            for i in range(self._start_index, self._start_index + safe_lines):
                item = self._items[i]
                table.add_row(f"{i:>{total_digits}}", self.__check_item(item))
            table.add_row(
                f"[red][{'.'*total_digits}][/]",
                f"[italic red]skipped {total - safe_lines } items...[/]",
            )
            last_row_number = total - self._start_index
            table.add_row(
                f"[{last_row_number:>{total_digits}}]",
                self.__check_item(item),
            )

        return table

    def __rich__(self) -> r.Panel:
        """Rich库渲染钩子，返回封装好的面板对象

        Returns:
            rich.Panel: 包含表格或空提示的面板
        """
        content = self.get_table() if self._items else r.Text("(empty)", style="dim")
        total = len(self._items)
        return r.Panel(
            content,
            title=self._title,
            subtitle=f"{total} items",
            title_align="left",
            subtitle_align="right",
            border_style=self._border_style,
        )
