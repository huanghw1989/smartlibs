from .filter import filter_no_null


def min_timeout(*timeout_vals):
    """最小timeout时间, None表示不限超时时间(即无穷大)

    Returns:
        float: 最小timeout时间
    """
    no_null_vals = list(filter_no_null(timeout_vals))
    
    if len(no_null_vals) == 0:
        return None
    elif len(no_null_vals) == 1:
        return no_null_vals[0]
    else:
        return min(*no_null_vals)