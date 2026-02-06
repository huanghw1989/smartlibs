from .value import is_not_null


def filter_no_null(val_iter):
    return filter(is_not_null, val_iter)