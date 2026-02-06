import json, traceback
from smart.aaas.__logger import logger
from redis import Redis

from smart.utils.template import template_str_eval


class BaseStateHook:
    def __init__(self, skip_on_err=False, **kwargs) -> None:
        self._opts = kwargs
        self._skip_on_err = skip_on_err
    
    def report(self, task_id, event, msg=None):
        logger.info("BaseStateHook.trigger %s, %s", event, msg)
        return True
    
    def close(self):
        pass

__hook_map = {}

def hook_cls(hook_type):
    def _hook_fn(hook_cls):
        __hook_map[hook_type] = hook_cls
    
    return _hook_fn

def get_hook_cls(hook_type, default_cls=None):
    if hook_type in __hook_map:
        return __hook_map[hook_type]
    elif default_cls:
        return default_cls
    else:
        logger.warning("miss StateHook type=%s", hook_type)
        return BaseStateHook

def get_hook(hook_type, default_cls=None, **kwargs):
    hook_cls = get_hook_cls(hook_type, default_cls=default_cls)
    return hook_cls(**kwargs)

def report_state(hook_dict_or_obj, task_id, event, msg=None, auto_close=False):
    if not hook_dict_or_obj:
        return None, None

    _close_hook = False
    if isinstance(hook_dict_or_obj, BaseStateHook):
        hook_obj = hook_dict_or_obj
    else:
        hook_type = hook_dict_or_obj.get('type')
        hook_obj = get_hook(hook_type, **hook_dict_or_obj)
        _close_hook = True

    try:
        return hook_obj.report(task_id, event, msg=msg), hook_obj
    except Exception as e:
        if not hook_obj._skip_on_err:
            logger.error("report_state %s error: %s", event, e)
            raise e
        else:
            logger.warning("report_state %s error: %s\n%s", event, e, traceback.format_exc())
            # logger.exception(e)
    finally:
        if auto_close and _close_hook:
            hook_obj.close()


@hook_cls('redis')
class RedisStateHook(BaseStateHook):
    DEFAULT_REDIS_OPTS = {
        'socket_timeout': 30,
        'socket_connect_timeout': 10,
        'retry_on_timeout': False
    }

    def __init__(self, host, port:int, state_key:str=None, state_key_format:str=None, state_ttl:int=3600, 
            password='', db=0, redis_kwargs:dict={}, **kwargs) -> None:
        assert state_key or state_key_format
        BaseStateHook.__init__(self, **kwargs)
        for k, v in self.DEFAULT_REDIS_OPTS.items():
            redis_kwargs.setdefault(k, v)
        self._redis = Redis(host, port, db, password, **redis_kwargs)
        self._state_key = state_key
        self._state_key_format = state_key_format
        self._state_ttl = state_ttl
    
    def _get_state_key(self, **kwargs):
        if self._state_key:
            return self._state_key
        elif self._state_key_format:
            return template_str_eval(self._state_key_format, mapping=kwargs)
        else:
            return None
    
    def report(self, task_id, event, msg=None):
        _state_key = self._get_state_key(task_id=task_id)
        if not _state_key:
            return False

        self._redis.rpush(
            _state_key,
            json.dumps({
                "event": event,
                "msg": msg,
            }, ensure_ascii=False)
        )
        if self._state_ttl is not None:
            self._redis.expire(_state_key, self._state_ttl)
        logger.debug("RedisStateHook.trigger key=%s, event=%s, ttl=%s", _state_key, event, self._state_ttl)
        return True
    
    def close(self):
        self._redis.close()