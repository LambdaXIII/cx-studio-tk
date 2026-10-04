"""字幕序列表（SubtitleSequence）——条目的排列容器。

内部以列表按开始时间排列条目，添加时尽力插入到时序位置；对外读取恒为
时序视图，并在条目时间被改写后于下一次读取时校正。容器不校验、不拒绝、
不改写交叠，也不携带元数据或名称。
"""

from bisect import insort
from collections.abc import Iterable, Iterator

from .item import SubtitleItem

__all__ = ["SubtitleSequence"]


def _start_milliseconds(item: SubtitleItem) -> int:
    """取条目起始时刻的毫秒值，作为排序与二分定位的键。"""
    return item.start.total_milliseconds


class SubtitleSequence:
    """按时间排列的字幕条目容器。

    添加只做尽力时序：以开始时间定位插入点，不检查交叠，也不拒绝任何条目
    （交叠条目原样共存）。内部排列不构成对外承诺——条目时间被改写后排列
    可能陈旧，因此迭代时先做一次有序性检查，发现乱序则就地稳定排序，
    保证每次读取都反映当前时序。

    条目按对象身份（``is``）匹配，不提供位置索引定位：排列不是稳定句柄，
    引用本身即句柄。
    """

    def __init__(self) -> None:
        self._items: list[SubtitleItem] = []

    def add(self, item: SubtitleItem) -> None:
        """把一个条目插入到时序位置（尽力，不检查交叠）。

        Args:
            item: 待加入的条目；容器持有其引用，不复制。
        """
        insort(self._items, item, key=_start_milliseconds)

    def add_from(self, items: Iterable[SubtitleItem]) -> None:
        """逐个加入可迭代来源中的所有条目。

        Args:
            items: 任意条目可迭代对象；逐个经由 ``add`` 加入。
        """
        for item in items:
            self.add(item)

    def take(self, item: SubtitleItem) -> SubtitleItem | None:
        """按对象身份把条目从本容器摘除并返回该实例。

        Args:
            item: 待取出的条目实例。

        Returns:
            SubtitleItem | None: 命中时返回该实例（已脱离本容器）；未命中
            返回 None，容器状态不变。
        """
        for index, existing in enumerate(self._items):
            if existing is item:
                del self._items[index]
                return existing
        return None

    def contains(self, item: SubtitleItem) -> bool:
        """按对象身份判断本容器是否持有该条目。

        Args:
            item: 待查询的条目实例。

        Returns:
            bool: 持有该实例返回 True，否则 False。
        """
        return any(existing is item for existing in self._items)

    def __iter__(self) -> Iterator[SubtitleItem]:
        self._ensure_sorted()
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, item: object) -> bool:
        return any(existing is item for existing in self._items)

    def _ordered_items(self) -> list[SubtitleItem]:
        """返回内部有序列表（不复制；必要时就地校正顺序）。

        Returns:
            list[SubtitleItem]: 按开始时间非降序排列的内部列表本身。
        """
        self._ensure_sorted()
        return self._items

    def _ensure_sorted(self) -> None:
        """有序性检查：发现起点乱序时就地稳定排序。"""
        items = self._items
        for index in range(1, len(items)):
            if _start_milliseconds(items[index - 1]) > _start_milliseconds(items[index]):
                items.sort(key=_start_milliseconds)
                return
