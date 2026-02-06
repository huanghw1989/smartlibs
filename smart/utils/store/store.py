import abc, inspect, threading, functools, enum
import time
from threading import Lock


from smart.utils.inspect import is_dict_or_dict_obj
from smart.utils.__logger import logger_utils


class ContextState(object):
    def __init__(self, name, state=None, update_state_op=None, lock:Lock=None):
        self.__state = state if state is not None else {}
        self.__name = name
        self.__update_state_op = update_state_op
        self.__lock = lock
        self.__readonly = False
    
    @property
    def name(self):
        return self.__name
    
    def set_readonly(self, readonly=True):
        """set state readonly

        Keyword Arguments:
            readonly {bool} -- whether the state is read only (default: {True})
        """
        self.__readonly = readonly
        
        return self

    def _find_op(self, key_path, on_found:callable, on_no_sub:callable=None, on_err_type=None):
        """按 key_path 查找字典操作
        
        Arguments:
            key_path {any} -- key路径, list|tuple类型会执行深度查找
            on_found {callable} -- fn(sub_obj, sub_key)->(b_update_state, value, *)
        
        Keyword Arguments:
            on_no_sub {callable} -- fn(sub_obj, sub_key) (default: {None})
            on_err_type {callable} -- fn(sub_obj, sub_key) (default: {None})
        
        Returns:
            tuple -- (hit, value) value 为 on_found 返回的结果的第二项值
        """
        if not key_path:
            return False, None

        if not isinstance(key_path, (tuple, list)):
            key_path = (key_path, )
            len_key_path = 1
        else:
            len_key_path = len(key_path)
        
        if len_key_path == 1:
            b_update_state, value, *_ = on_found(self.__state, key_path[0])

            return True, value
        
        obj = self.__state

        update_state_op = self.__update_state_op
        _founded_list = []

        for i in range(len_key_path-1):
            sub_key = key_path[i]
            sub_obj = None

            if sub_key not in obj:
                if on_no_sub:
                    on_no_sub(obj, sub_key)
                    
                if sub_key in obj:
                    sub_obj = obj[sub_key]
            else:
                sub_obj = obj[sub_key]
            
            if sub_obj is None:
                return False, None

            is_dict = is_dict_or_dict_obj(sub_obj)
            if not is_dict and on_err_type:
                on_err_type(obj, sub_key)
                sub_obj = obj[sub_key]
                is_dict = is_dict_or_dict_obj(sub_obj)
            
            if not is_dict:
                return False, None
            
            if update_state_op:
                _founded_list.insert(0, (obj, sub_key, sub_obj))

            obj = sub_obj

        b_update_state, value, *_ = on_found(obj, key_path[-1])

        if update_state_op and b_update_state:
            if self.__readonly:
                logger_utils.warning('state {} is readonly'.format(self.__name))
            else:
                for f_obj, f_k, f_v in _founded_list:
                    update_state_op(f_obj, f_k, f_v)

        return True, value

    def get(self, key_path, default_val=None):
        """get state

        Arguments:
            key_path {str|list|tuple} -- key path
            default_val {any} -- default value

        Returns:
            any -- value
        """
        hit, rst = self._find_op(key_path, 
            on_found = lambda obj, key: (False, obj.get(key, default_val))
            )

        if hit:
            return rst
        else:
            return default_val
    
    def wait(self, key_path, timeout=0):
        sleep_ts = 1
        begin_ts = time.time()
        while True:
            hit, rst = self._find_op(key_path, 
                on_found = lambda obj, key: (False, obj.get(key, None))
                )
            
            if hit:
                return rst
            else:
                time.sleep(sleep_ts/1000)

                if timeout:
                    if time.time() - begin_ts > timeout:
                        raise TimeoutError('wait state {} timeout'.format(str(key_path)))

                sleep_ts = min(sleep_ts+5, 5000)

    def set(self, key_path, value):
        """set state

        Arguments:
            key_path {str|list|tuple} -- key path
            value {any} -- value
        """
        hit, rst = self._find_op(
            key_path, 
            on_found = lambda obj, key: (True, True, obj.__setitem__(key, value)),
            on_no_sub = lambda obj, key: obj.__setitem__(key, {})
            )

        return rst

    def delete(self, key_path):
        """delete state

        Arguments:
            key_path {str|list|tuple} -- key path
        """
        hit, rst = self._find_op(
            key_path, 
            on_found = lambda obj, key: (True, key in obj and obj.__delitem__(key))
            )

    def get_or_set(self, key_path, default_val):
        """get state if exist, or set value

        Arguments:
            key_path {str|list|tuple} -- key path
            default_val {any} -- default value

        Returns:
            any -- value
        """
        lock = self.__lock

        try:
            if lock:
                lock.acquire()

            hit, rst = self._find_op(
                key_path, 
                lambda obj, key: (key not in obj, obj.get(key, default_val), key not in obj and obj.__setitem__(key, default_val)),
                lambda obj, key: (True, True, obj.__setitem__(key, {}))
                )
        finally:
            if lock:
                lock.release()

        if hit:
            return rst
        else:
            return default_val
    
    def __get_or_set_fn_op(self, obj, key, val_fn):
        if key in obj:
            return False, obj[key]
        
        obj[key] = val = val_fn()

        return True, val

    def get_or_set_fn(self, key_path, val_fn):
        """get state if exist, or set value by val_fn()

        Arguments:
            key_path {str|list|tuple} -- key path
            val_fn {callable} -- val function ()->any

        Returns:
            any -- value
        """
        lock = self.__lock

        try:
            if lock:
                lock.acquire()
            
            hit, rst = self._find_op(
                key_path, 
                functools.partial(self.__get_or_set_fn_op, val_fn=val_fn),
                lambda obj, key: (True, True, obj.__setitem__(key, {}))
                )
        finally:
            if lock:
                lock.release()

        return rst

    def set_fn(self, key_path, val_fn):
        """set state by val_fn(old_value)

        Arguments:
            key_path {str|list|tuple} -- key path
            val_fn {callable} -- val function (old_value)->any

        Returns:
            any -- value
        """
        lock = self.__lock

        def _set_fn(obj, key):
            old_val = obj.get(key)
            value = val_fn(old_val)
            obj[key] = value
            
            return True, value

        try:
            if lock:
                lock.acquire()
            
            hit, rst = self._find_op(
                key_path, 
                on_found = _set_fn,
                on_no_sub = lambda obj, key: (True, True, obj.__setitem__(key, {}))
                )
        finally:
            if lock:
                lock.release()

        return rst
    
    def to_dict(self):
        return dict(self.__state)
    
    def update(self, state_dict):
        if state_dict:
            for k, v in state_dict.items():
                self.set(k, v)


class ContextValue:
    def __init__(self, value_dict, name):
        self.__value_dict = value_dict
        self.__name = name
    
    def get(self, default_val=None):
        return self.__value_dict.get(self.__name, default_val)
    
    def set(self, val):
        self.__value_dict[self.__name] = val
    
    def delete(self):
        del self.__value_dict[self.__name]


class StoreTypes(enum.Enum):
    state = 0
    list = 1
    dict = 2
    lock = 3
    value = 4

    @property
    def key_ns(self):
        return self.value


class BaseContextStore:
    def __init__(self):
        self.__ctx_values = {}
    
    def state(self, name) -> ContextState:
        pass
    
    def list(self, name) -> list:
        pass

    def dict(self, name) -> dict:
        pass
    
    def lock(self, name) -> Lock:
        pass

    def _value(self, name) -> ContextValue:
        pass
    
    def value(self, name) -> ContextValue:
        ctx_val = self.__ctx_values.get(name)

        if ctx_val is None:
            self.__ctx_values[name] = ctx_val = self._value(name)
        
        return ctx_val
    
    def get_names(self, type:StoreTypes) -> list:
        """获取指定类型store的所有名称
        
        Arguments:
            type {StoreTypes|str} -- store类型
        
        Returns:
            list -- names
        """
        pass
    
    def close(self):
        pass


class ContextStore(BaseContextStore):
    def __init__(self):
        self.__stores = {}

        BaseContextStore.__init__(self)
    
    def __get_store(self, type:StoreTypes):
        store = self.__stores.get(type.key_ns)

        if store is None:
            self.__stores[type.key_ns] = store = {}
        
        return store

    def state(self, name) -> ContextState:
        store = self.__get_store(StoreTypes.state)
        state = store.get(name)

        if state is None:
            store[name] = state = ContextState(name)
        
        return state
    
    def list(self, name) -> list:
        store = self.__get_store(StoreTypes.list)
        _list = store.get(name)

        if _list is None:
            store[name] = _list = []
        
        return _list
    
    def dict(self, name) -> dict:
        store = self.__get_store(StoreTypes.dict)
        _dict = store.get(name)

        if _dict is None:
            store[name] = _dict = {}
        
        return _dict

    def lock(self, name) -> Lock:
        store = self.__get_store(StoreTypes.lock)
        _lock = store.get(name)

        if _lock is None:
            store[name] = _lock = Lock()
        
        return _lock
    
    def _value(self, name) -> ContextValue:
        store = self.__get_store(StoreTypes.value)

        return ContextValue(store, name)
    
    def get_names(self, type:StoreTypes):
        if isinstance(type, str):
            type = getattr(StoreTypes, type)
        
        store:dict = self.__get_store(type)

        return list(store.keys())