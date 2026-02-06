import inspect, functools
from inspect import FullArgSpec

from smart.utils import cast
from smart.utils.bound import Bound, BaseBound
from smart.utils.__logger import logger_utils


def __cast_val(val, val_class):
    if val is None: return val

    if inspect.isclass(val_class):
        cls_name = val_class.__name__ if val_class else None
    else:
        cls_name = None

    try:
        return cast.cast_val(cls_name, val)
    except:
        logger_utils.warning('val %s cannot be cast to %s', val, val_class)
        return None


def __cast_kwargs_by_annotations(spec:FullArgSpec, kwargs:dict):
    annotations = spec.annotations or {}

    for key, val in kwargs.items():
        val_class = annotations.get(key)

        if val_class:
            kwargs[key] = __cast_val(val, val_class)

    return kwargs


def __cast_args_by_annotations(spec:FullArgSpec, args:list, offset=0):
    annotations = spec.annotations or {}
    arg_keys = spec.args

    if isinstance(args, tuple):
        args = list(args)

    for i, val in enumerate(args):
        key = arg_keys[i + offset]
        val_class = annotations.get(key)

        if val_class:
            args[i] = __cast_val(val, val_class)

    return args


def resolve_func_args(func:callable, args:list=[], kwargs:dict={}):
    if (not args) and (not kwargs):
        return [], {}

    if isinstance(func, BaseBound):
        return resolve_func_args(func.__func__, args, kwargs)
    else:
        # smart.utils.bound.once_fn
        real_func = getattr(func, '__real_func__', None)
        if callable(real_func):
            return resolve_func_args(real_func, args, kwargs)

    spec = inspect.getfullargspec(func)
    arg_offset = 1 if inspect.ismethod(func) or isinstance(func, Bound) else 0
    
    if not spec.varargs:
        max_arg_num = len(spec.args) - arg_offset
        args = args[:max_arg_num]

    if not spec.varkw:
        kwargs = {
            key: val
            for key, val in kwargs.items()
            if key in spec.args
        }
    
    return __cast_args_by_annotations(spec, args, offset=arg_offset), __cast_kwargs_by_annotations(spec, kwargs)


def func_safe_call(func:callable, args:list=[], kwargs:dict={}):
    args, kwargs = resolve_func_args(func, args, kwargs)
    return func(*args, **kwargs)


def func_safe_bind(func, args:list=[], kwargs:dict={}):
    args, kwargs = resolve_func_args(func, args, kwargs)
    return functools.partial(func, *args, **kwargs)

