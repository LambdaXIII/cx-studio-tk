def limit_number(
    x, bottom: float | int | None = None, top: float | int | None = None, cls=None
):
    """
    Limits a number to a given range.

    'None' edge is ignored.
    """
    result = x
    if bottom is not None:
        result = max(result, bottom)
    if top is not None:
        result = min(result, top)
    return result if cls is None else cls(result)


def map_number(x, in_min, in_max, out_min=0.0, out_max=1.0, cls=float):
    """
    Maps a number from one range to another.

    Same with the function in AE.
    """
    result = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return result if cls is None else cls(result)
