import functools
import multiprocessing as mp
from multiprocessing.managers import SyncManager, DictProxy
from threading import Lock

from smart.utils.dict import dict_safe_set, dict_safe_get, dict_get_or_set

from smart.utils.store.store import ContextState, BaseContextStore, ContextValue, StoreTypes
from smart.utils.__logger import logger_utils


class MpState(ContextState):
    def __init__(self, name, state, lock=None):
        self.__state = state
        self.__lock:Lock = lock

        ContextState.__init__(self, name, state=state, update_state_op=self._update_state_op, lock=lock)
    
    @staticmethod
    def _update_state_op(obj, key, val):
        if isinstance(obj, DictProxy):
            obj[key] = val


class MpContextStore(BaseContextStore):
    def __init__(self):
        BaseContextStore.__init__(self)

        manager = SyncManager()

        self._manager = manager
        manager.start()
        
        self.__store = manager.dict()
        self.__store_lock = manager.RLock()
    
    @property
    def store_dict(self):
        return self.__store
    
    @property
    def manager(self):
        if self._manager is None:
            self._manager = mp.Manager()

        return self._manager
    
    def __store_get(self, key, val_fn, val_fn_args=None):
        val = self.__store.get(key)

        if val is None:
            # with mp.Lock():
            with self.__store_lock:
                val = self.__store.get(key)

                if val is None:
                    if val_fn_args is None:
                        val = val_fn()
                    else:
                        val = val_fn(*val_fn_args)

                    self.__store[key] = val

        return val
    
    def __new_state(self, name):
        # logger_utils.debug('MpContextStore.__new_state %s', name)
        return MpState(
            name, 
            state = self.manager.dict(),
            lock = self.manager.RLock()
            # state = self.dict(('__state__', name)),
            # lock = self.lock(('__state__', name))
        )

    def state(self, name) -> MpState:
        return self.__store_get((StoreTypes.state.key_ns, name), self.__new_state, (name,))
    
    def list(self, name) -> list:
        return self.__store_get((StoreTypes.list.key_ns, name), self.manager.list)
    
    def dict(self, name) -> dict:
        return self.__store_get((StoreTypes.dict.key_ns, name), self.manager.dict)
    
    def lock(self, name) -> Lock:
        return self.__store_get((StoreTypes.lock.key_ns, name), self.manager.RLock)
    
    def _value(self, name) -> ContextValue:
        return ContextValue(self.__store, (StoreTypes.value.key_ns, name))

    def get_names(self, type:StoreTypes):
        if isinstance(type, str):
            type = getattr(StoreTypes, type)
        
        names = []
        for key in self.__store.keys():
            ns, name = key
            if ns == type.key_ns:
                names.append(name)
        
        return names

    def __getstate__(self):
        """spawn 模式的多进程会使用 pickle 序列化本实例, 但 SyncManager 不是 pickable 对象, 需排除
        """
        _dict = self.__dict__.copy()
        _dict.update(_manager=None)
        return _dict
    
    def __setstate__(self, state):
        self.__dict__.update(state)
    
    def close(self):
        self.manager.shutdown()