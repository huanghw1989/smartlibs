import inspect


def is_dict_or_dict_obj(obj):
    if isinstance(obj, dict):
        return True
    
    if obj is None:
        return False
    
    if isinstance(obj, (list, tuple, set, int, float)):
        return False
    
    if inspect.isclass(obj):
        return False
    
    return all(
        hasattr(obj, attr)
        for attr in ('__contains__', '__getitem__', '__setitem__', '__delitem__', '__dict__')
    )