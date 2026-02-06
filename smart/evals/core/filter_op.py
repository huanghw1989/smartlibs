from typing import Any
from smart.utils.dict import dict_find
from smart.utils.list import list_safe_iter
from smart.utils.number import safe_parse_float


def op_not(fn):
    def _fn(item):
        return not fn(item)
    return _fn


class FilterFn:
    def __init__(self, fn) -> None:
        self._fn = fn
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self._fn(*args, **kwds)


class FilterOp:
    def val_eq(self, key_path, value):
        return FilterFn(lambda item: dict_find(item, key_path) == value)
    
    def val_in(self, key_path, value_list:list):
        return FilterFn(lambda item: dict_find(item, key_path) in value_list)
    
    def val_not_in(self, key_path, value_list:list):
        return FilterFn(lambda item: dict_find(item, key_path) not in value_list)
    
    def val_in_range(self, key_path, start=None, end=None, cast_fn:callable=None):
        """item的key_path对应值, 是否在[start, end]区间内; start/end为None时代表不限制

        Args:
            key_path (str|list): item的key_path
            start (any, optional): 值>=start; None则不匹配. Defaults to None.
            end (any, optional): 值<=end; None则不匹配. Defaults to None.
            cast_fn (callable, optional): 值转换格式. Defaults to None.

        Returns:
            FilterFn: 过滤函数
        """
        if cast_fn == 'float': cast_fn = safe_parse_float
        def _cb(item):
            value = dict_find(item, key_path)
            if cast_fn:
                value = cast_fn(value)
            if value is None:
                return False
            if start is not None and value < start:
                return False
            if end is not None and value > end:
                return False
            return True
        return FilterFn(_cb)
    
    def list_contain(self, key_path, value_or_list):
        return FilterFn(lambda item: any(
            (value in dict_find(item, key_path) for value in list_safe_iter(value_or_list))
        ))
    
    def startswith(self, key_path, prefix_str_or_list):
        def _fn(item):
            value = str(dict_find(item, key_path, ''))
            for prefix in list_safe_iter(prefix_str_or_list):
                if value.startswith(prefix):
                    return True
            return False
        return FilterFn(_fn)

    def endswith(self, key_path, suffix_str_or_list):
        def _fn(item):
            value = str(dict_find(item, key_path, ''))
            for suffix in list_safe_iter(suffix_str_or_list):
                if value.endswith(suffix):
                    return True
            return False
        return FilterFn(_fn)
    
    def all(self, filter_fn_list:list):
        return FilterFn(lambda item: all((filter_fn(item) for filter_fn in filter_fn_list)))

    def any(self, filter_fn_list:list):
        return FilterFn(lambda item: any((filter_fn(item) for filter_fn in filter_fn_list)))
    
    def _not(self, fn:list):
        return FilterFn(lambda item: not fn(item))