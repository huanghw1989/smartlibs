import functools


class BaseBound:
    def __init__(self, func:callable):
        self.__func__ = func
        self.__name__ = getattr(func, '__name__', str(func))
        self.__doc__ = getattr(func, '__doc__', None)
    
    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)


class Bound(BaseBound):
    def __init__(self, obj, func:callable):
        BaseBound.__init__(self, func)
        self.__self__ = obj
    
    def __call__(self, *args, **kwargs):
        return self.__func__(self.__self__, *args, **kwargs)


class BoundFn(BaseBound):
    def __init__(self, func:callable):
        BaseBound.__init__(self, func)
        self.__fn_args = None
        self.__fn_kwargs = None
    
    def bind(self, *args, **kwargs):
        self.__fn_args = args
        self.__fn_kwargs = kwargs
        return self
    
    @property
    def bind_args(self):
        _args = self.__fn_args

        if _args is None:
            _args = []

        return _args
    
    @property
    def bind_kwargs(self):
        _kwargs = self.__fn_kwargs

        if _kwargs is None:
            _kwargs = {}
        
        return _kwargs

    def __call__(self, *args, **kwargs):
        if self.__fn_args:
            args = [*self.__fn_args, *args]

        if self.__fn_kwargs:
            kwargs = {**self.__fn_kwargs, **kwargs}

        return self.__func__(*args, **kwargs)


class OnceFn(BoundFn):
    def __init__(self, func:callable):
        BoundFn.__init__(self, func)
        self.__rst = None
        
    def __call__(self, *args, **kwargs):
        if self.__rst is None:
            self.__rst = BoundFn.__call__(self, *args, **kwargs)
        return self.__rst
    
    @property
    def result(self):
        return self.__rst

def _set_real_func(bound_fn, ori_fn):
    setattr(bound_fn, '__real_func__', ori_fn)

def once_fn(func, *fn_args, **fn_kwargs):
    fn = OnceFn(func).bind(*fn_args, **fn_kwargs)

    def _once_call(*args, **kwargs):
        return fn(*args, **kwargs)
    
    _set_real_func(_once_call, func)
    return _once_call

def once_fn_builder(*fn_args, **fn_kwargs):

    return functools.partial(once_fn, *fn_args, **fn_kwargs)