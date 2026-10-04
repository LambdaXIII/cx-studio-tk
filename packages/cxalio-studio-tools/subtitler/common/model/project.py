"""字幕项目（SubtitleProject）——把条目组织为多个不交叠序列的容器。

新增条目按创建序依次尝试各序列的不交叠容纳位置，全部容不下时自动新增序列；
同时提供跨序列的全量时序读取与通用元数据容器。不交叠是组织行为的结果而非
校验不变量：绕过本容器入口（直接操作序列、改写已入列条目的时间）产生的交叠
被容忍。
"""

from bisect import bisect_left
from collections.abc import Iterable, Iterator
from typing import Any

from .item import SubtitleItem
from .sequence import SubtitleSequence

__all__ = ["SubtitleProject"]


def _start_milliseconds(item: SubtitleItem) -> int:
    """取条目起始时刻的毫秒值，作为二分定位的键。"""
    return item.start.total_milliseconds


class SubtitleProject:
    """持有有序序列集合，并把新增条目路由到不交叠位置的容器。

    序列的排列序即创建序，新增序列追加在尾部。条目入列时按创建序依次尝试各
    序列：在序列内以开始时间二分找到时序位置，与相邻条目做严格交叠判定
    （端点相触不算交叠），首个能容纳的序列即收下；全部序列都容不下时自动
    新增一个序列。

    读取面提供 Item 级的跨序列全量时序流与实例身份查询，不需要经所属序列
    二跳取得条目。条目按对象身份（``is``）匹配，不提供位置索引或 id 句柄。
    """

    def __init__(self) -> None:
        self._sequences: list[SubtitleSequence] = []
        self.meta: dict[str, Any] = {}

    def add(self, item: SubtitleItem) -> None:
        """把一个条目路由到首个能容纳它的序列，全部容不下则新增序列。

        Args:
            item: 待加入的条目；容器持有其引用，不复制。
        """
        for sequence in self._sequences:
            if self._can_place(sequence, item):
                sequence.add(item)
                return
        sequence = SubtitleSequence()
        sequence.add(item)
        self._sequences.append(sequence)

    def add_from(self, items: Iterable[SubtitleItem]) -> None:
        """逐个路由可迭代来源中的所有条目。

        Args:
            items: 任意条目可迭代对象；逐个经由 ``add`` 加入。
        """
        for item in items:
            self.add(item)

    def take(self, item: SubtitleItem) -> SubtitleItem | None:
        """按对象身份把条目从所属序列摘除并返回该实例。

        Args:
            item: 待取出的条目实例。

        Returns:
            SubtitleItem | None: 命中时返回该实例（已脱离本项目）；未命中
            返回 None，容器状态不变。
        """
        for sequence in self._sequences:
            found = sequence.take(item)
            if found is not None:
                return found
        return None

    def contains(self, item: SubtitleItem) -> bool:
        """按对象身份判断本项目是否持有该条目。

        Args:
            item: 待查询的条目实例。

        Returns:
            bool: 持有该实例返回 True，否则 False。
        """
        return any(sequence.contains(item) for sequence in self._sequences)

    @property
    def sequences(self) -> tuple[SubtitleSequence, ...]:
        """返回全部序列，按创建序。

        Returns:
            tuple[SubtitleSequence, ...]: 序列元组（创建序即排列序）。
        """
        return tuple(self._sequences)

    def __iter__(self) -> Iterator[SubtitleItem]:
        merged: list[SubtitleItem] = [
            item for sequence in self._sequences for item in sequence
        ]
        merged.sort(key=_start_milliseconds)
        return iter(merged)

    def __len__(self) -> int:
        return sum(len(sequence) for sequence in self._sequences)

    def __contains__(self, item: object) -> bool:
        return any(item in sequence for sequence in self._sequences)

    def _can_place(self, sequence: SubtitleSequence, item: SubtitleItem) -> bool:
        """判断某序列能否在不与既有条目交叠的前提下容纳该条目。

        Args:
            sequence: 待尝试的序列。
            item: 待安置的条目。

        Returns:
            bool: 序列内存在无交叠容纳位置返回 True，否则 False。
        """
        items = sequence._ordered_items()
        start_ms = _start_milliseconds(item)
        position = bisect_left(items, start_ms, key=_start_milliseconds)
        # 起点相同的条目可能共存（零时长条目彼此不算交叠），先越过它们
        # 逐一检查，再取其后的首个更晚条目。
        index = position
        while index < len(items) and _start_milliseconds(items[index]) == start_ms:
            if item.time_range.is_overlapped_with(items[index].time_range):
                return False
            index += 1
        if position > 0 and item.time_range.is_overlapped_with(
            items[position - 1].time_range
        ):
            return False
        if index < len(items) and item.time_range.is_overlapped_with(
            items[index].time_range
        ):
            return False
        return True
