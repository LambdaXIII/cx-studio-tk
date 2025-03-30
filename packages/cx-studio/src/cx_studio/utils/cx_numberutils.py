from numbers import Number


def limit_number(x, min: Number = None, max: Number = None, cls=None):
    """
    Limits a number to a given range.
    :param x: The number to limit.
    :param min: The minimum value. If None, no minimum is applied.
    :param max: The maximum value. If None, no maximum is applied.
    :param cls: The class to return the result as. If None, the result is returned as input.
    :return: The limited number.
    """
    result = x
    if min is not None:
        result = max(result, min)
    if max is not None:
        result = min(result, max)
    return result if cls is None else cls(result)


def map_number(x, in_min, in_max, out_min=0.0, out_max=1.0, cls=float):
    """
    Maps a number from one range to another.
    :param x: The number to map.
    :param in_min: The minimum value of the input range.
    :param in_max: The maximum value of the input range.
    :param out_min: The minimum value of the output range.
    :param out_max: The maximum value of the output range.
    :param cls: The class to return the result as. If None, the result is returned as input.
    :return: The mapped number.
    """
    result = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return result if cls is None else cls(result)
