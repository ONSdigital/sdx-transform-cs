def merge_dicts(*args):
    """Makes it possible to merge any number of non-nested dicts on Python 3.4."""
    z = args[0].copy()

    for x in args:
        z.update(x)
    return z
