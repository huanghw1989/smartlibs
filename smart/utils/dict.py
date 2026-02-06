from copy import deepcopy

from .list import list_safe_iter, list_safe_get


class DictMerger:
    def __init__(self, extra_fns=None, no_copy=False, merge_list=False, append_list=False):
        self.no_copy = no_copy
        self.extra_fns = list(extra_fns or [])

        if merge_list or append_list:
            self.extra_fns.append(
                self.merge_list_fn_builder(append_mode=append_list) )
    
    def merge_list_fn_builder(self, append_mode=True):
        def merge_list(list_a, list_b, context_keys):
            if any(not isinstance(l, (list, tuple)) for l in (list_a, list_b)):
                return False, None
            
            if isinstance(list_a, tuple):
                list_a = list(list_a)
            
            if append_mode:

                list_a.extend(list_b)
            else:

                len_a = len(list_a)

                for i, val in enumerate(list_b):
                    if i < len_a:
                        list_a[i] = val
                    else:
                        list_a.append(val)
            
            return True, list_a
        
        return merge_list

    
    def deep_merge(self, dict_a:dict, dict_b:dict, context_keys=None):
        if not dict_a:
            if self.no_copy and dict_a is not None:
                dict_a.update(deepcopy(dict_b))
                return dict_a
                
            return deepcopy(dict_b)
        
        dict_merged = dict_a if self.no_copy else deepcopy(dict_a)

        if not dict_b:
            return dict_merged
        
        if any(not isinstance(d, dict) for d in (dict_a, dict_b)):

            for extra_fn in self.extra_fns:
                can_merge, merge_rst = extra_fn(dict_merged, dict_b, context_keys) or (False, None)
                
                if can_merge:
                    return merge_rst
            
            return deepcopy(dict_b)
        else:

            context_keys = context_keys or tuple()

            for k, v in dict_b.items():
                if k in dict_merged:
                    dict_merged[k] = self.deep_merge(dict_merged[k], v, context_keys=tuple((*context_keys, k)))
                else:
                    dict_merged[k] = deepcopy(v)
            
            return dict_merged


def dict_deep_merge(dict_a:dict, dict_b:dict, no_copy=False) -> dict:
    """深度合并两个dict. 当key冲突时，dict_b的值覆盖dict_a
    
    Arguments:
        dict_a {dict} -- one dict
        dict_b {dict} -- another dict
    
    Keyword Arguments:
        no_copy {bool} -- 如果为True, 将直接merge结果到dict_a (default: {False})
    
    Returns:
        dict -- merged dict
    """
    return DictMerger(no_copy=no_copy).deep_merge(dict_a, dict_b)
    # if not dict_a or not isinstance(dict_a, dict):
    #     return deepcopy(dict_b)

    # dict_merged = dict_a if no_copy else deepcopy(dict_a)

    # if not dict_b or not isinstance(dict_b, dict):
    #     return dict_merged

    # for k, v in dict_b.items():
    #     if k in dict_merged:
    #         dict_merged[k] = dict_deep_merge(dict_merged[k], v, no_copy=no_copy)
    #     else:
    #         dict_merged[k] = deepcopy(v)

    # return dict_merged


def dict_pop(obj, filter_func:callable):
    filter_obj = dict(
        filter(
            lambda x: filter_func(x[0], x[1]),
            obj.items()
        )
    )

    for k in filter_obj.keys():
        obj.pop(k)

    return filter_obj


def dict_safe_get(obj, key, default_val=None):
    if not obj:
        return default_val

    for k in list_safe_iter(key):
        if hasattr(obj, '__getitem__') and k in obj:
            obj = obj[k]
        else:
            return default_val

    return obj


def dict_find(obj, key_path, default_val=None):
    if not obj:
        return default_val

    for k in list_safe_iter(key_path):
        if isinstance(obj, (list, tuple)):
            if isinstance(k, int) and k < len(obj) and k >= -len(obj):
                obj = obj[k]
            else:
                return default_val
        elif hasattr(obj, '__getitem__') and k in obj:
            obj = obj[k]
        else:
            return default_val

    return obj


def __sub_obj_setter(obj, keys):
    if len(keys) < 2:
        return obj, list_safe_get(keys, 0)
    
    for i in range(0, len(keys)-1):
        key = keys[i]

        if not hasattr(obj, '__getitem__'):
            return None, keys[i:]
        
        subobj = obj.get(key) if isinstance(obj, dict) else obj.__getitem__(key)

        if subobj is None:
            obj[key] = subobj = {}

        obj = subobj
    
    return obj, keys[-1]


def dict_safe_set(obj, key_val_or_list, val):
    assert hasattr(obj, '__getitem__')
    
    if isinstance(key_val_or_list, (list, tuple)):
        obj, key = __sub_obj_setter(obj, key_val_or_list)
    else:
        key = key_val_or_list
    
    if obj is None:
        raise ValueError('dict key conflict', obj, key_val_or_list)

    obj[key] = val


def dict_get_or_set(obj:dict, key_val_or_list, default_val=None, raise_err_on_fail=True):
    assert hasattr(obj, '__getitem__')

    if isinstance(key_val_or_list, (list, tuple)):
        obj, key = __sub_obj_setter(obj, key_val_or_list)
    else:
        key = key_val_or_list
    
    if obj is not None:

        if key not in obj:
            obj[key] = default_val
        
        return obj[key]
    elif raise_err_on_fail:
        
        raise ValueError('dict key conflict', obj, key_val_or_list)

    return default_val