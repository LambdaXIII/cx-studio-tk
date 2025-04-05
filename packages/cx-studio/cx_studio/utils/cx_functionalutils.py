def flatten_list(*args):
    for arg in args:
        if isinstance(arg, list | tuple | set):
            yield from flatten_list(*arg)
