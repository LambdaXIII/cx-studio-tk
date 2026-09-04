"""通用的序列处理工具函数。

提供扁平化（flatten_list）、元素间插分隔值（iter_with_separator）
与按谓词二分拆分（split_to_two）三个纯函数，不依赖具体业务类型。
"""

from collections.abc import Iterable, Callable, Iterator
from typing import Any


def flatten_list(*args: Any) -> Iterator[Any]:
    """把多个入参中的可迭代对象递归展开为扁平序列。

    字符串（str）视为叶子节点，不会被拆成单个字符；其余可迭代对象
    （列表、元组、生成器等）递归展开到最内层元素为止。

    Args:
        *args: 任意数量的元素或任意嵌套的可迭代对象。

    Yields:
        按原顺序逐个产出的叶子元素。
    """
    for arg in args:
        if isinstance(arg, Iterable) and not isinstance(arg, str):
            yield from flatten_list(*arg)
        else:
            yield arg


def iter_with_separator(iterable: Iterable[Any], sep: Any) -> Iterable[Any]:
    """在可迭代对象的相邻元素之间插入分隔值后逐个产出。

    分隔值只出现在元素与元素之间，不会出现在序列开头或结尾。

    Args:
        iterable: 被遍历的可迭代对象。
        sep: 插入在相邻元素之间的分隔值（任意类型）。

    Yields:
        元素与分隔值交替产出，第一个和最后一个产出必为元素。
    """
    for i, item in enumerate(iterable):
        if i > 0:
            yield sep
        yield item


def split_to_two(
    iterable: Iterable[Any], predicate: Callable[[Any], bool]
) -> tuple[list[Any], list[Any]]:
    """按谓词把可迭代对象拆分为两个列表。

    每个元素只落入一个列表：满足谓词的元素进入第一个列表，不满足的
    进入第二个列表，两者均保持原遍历顺序。

    Args:
        iterable: 被拆分的可迭代对象。
        predicate: 对每个元素调用并返回 bool 的判断函数。

    Returns:
        tuple[list[Any], list[Any]]: 二元组 ``(yes, no)``：
            - yes: predicate 返回真值的元素列表；
            - no: predicate 返回假值的元素列表。
    """
    yes, no = [], []
    for x in iterable:
        if predicate(x):
            yes.append(x)
        else:
            no.append(x)
    return yes, no
