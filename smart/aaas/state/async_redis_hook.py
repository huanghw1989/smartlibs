from .state_hook import BaseStateHook, logger
import asyncio, json

class AsyncRedisHook(BaseStateHook):
    DEFAULT_REDIS_OPTS = {
        'socket_timeout': 30,
        'socket_connect_timeout': 10,
        'auto_reconnect': False
    }

    def __init__(self, host, port:int, state_key:str, state_ttl:int=3600, 
            password='', db=0, redis_kwargs:dict={}, **kwargs) -> None:
        BaseStateHook.__init__(self, **kwargs)
        for k, v in self.DEFAULT_REDIS_OPTS.items():
            redis_kwargs.setdefault(k, v)
        self._redis_args = {
            'host': host,
            'port': port,
            'password': password,
            'db': db,
            'auto_reconnect': redis_kwargs.get('auto_reconnect')
        }
        self._redis_opts = redis_kwargs
        self.__conn = None
        self._state_key = state_key
        self._state_ttl = state_ttl
        import asyncio_redis
        self._pool = asyncio_redis.Pool
    
    async def _redis_conn(self):
        if self.__conn is None:
            _timeout = self._redis_opts.get('socket_connect_timeout')
            self.__conn = await asyncio.wait_for(
                self._pool.create(**self._redis_args),
                _timeout
            )
        return self.__conn
    
    async def _redis_query(self, query_fn, *args):
        _timeout = self._redis_opts.get('socket_timeout')
        return await asyncio.wait_for(
            query_fn(*args),
            _timeout
        )

    async def report(self, task_id, event, msg=None):
        logger.info("AsyncRedisHook.trigger %s, %s", event, msg)
        _redis = await self._redis_conn()
        is_success = await self._redis_query(
            _redis.rpush,
            self._state_key,
            (json.dumps({
                "event": event,
                "msg": msg,
            }, ensure_ascii=False),)
        )
        if is_success:
            if self._state_ttl is not None:
                await self._redis_query(_redis.expire, self._state_key, self._state_ttl)
        else:
            logger.warning("AsyncRedisHook redis.rpush failed, state=%s, event=%s", self._state_key, event)
        return True
    
    def close(self):
        if self.__conn is not None:
            self.__conn.close()
            self.__conn = None