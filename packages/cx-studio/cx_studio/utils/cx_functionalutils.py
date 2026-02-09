from collections.abc import Iterable, Callable
from typing import Any


def flatten_list(*args):
    for arg in args:
        if isinstance(arg, Iterable) and not isinstance(arg, str):
            yield from flatten_list(*arg)
        else:
            yield arg


def iter_with_separator(iterable: Iterable, sep):
    for i, item in enumerate(iterable):
        if i > 0:
            yield sep
        yield item


def split_to_two(
    iterable: Iterable, yew_or_no: Callable[[Any], bool]
) -> tuple[list, list]:
    """Split iterable into two lists,
    one with items that satisfy the predicate,
    and the other with items that do not.

    params:
        iterable: Iterable to split
        yew_or_no: Callable that returns True or False
    """
    yes, no = [], []
    for x in iterable:
        if yew_or_no(x):
            yes.append(x)
        else:
            no.append(x)
    return yes, no
