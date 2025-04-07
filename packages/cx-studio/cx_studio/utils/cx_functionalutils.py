from collections.abc import Iterable, Sequence


def flatten_list(*args):
    for arg in args:
        if isinstance(arg, list | tuple | set):
            yield from flatten_list(*arg)


def iter_with_separator(iterable: Sequence | Iterable, sep):
    for i, item in enumerate(iterable):
        if i > 0:
            yield sep
        yield item
