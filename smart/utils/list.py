import types


def list_safe_iter(list_or_val):
    if isinstance(list_or_val, (list, tuple)):
        
        for val in list_or_val:
            yield val
    else:

        yield list_or_val


def list_safe_get(arr, idx, default_val=None):
    if idx >=0 and idx < len(arr):
        return arr[idx]
    else:
        return default_val


def list_to_tuple(val, deep:int=-1):
    if isinstance(val, (list, types.GeneratorType)):
        if deep:
            return tuple(
                list_to_tuple(c_val, deep=deep-1)
                for c_val in val
            )
        else:
            return tuple(val)
    else:
        return val