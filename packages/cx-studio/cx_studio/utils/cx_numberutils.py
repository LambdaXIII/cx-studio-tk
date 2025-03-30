from typing import Number


def limit_number(x, min: Number = None, max: Number = None, cls=None):
    result = x
    if min is not None:
        result = max(result, min)
    if max is not None:
        result = min(result, max)
    return result if cls is None else cls(result)
