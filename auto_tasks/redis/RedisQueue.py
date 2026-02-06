from redis import Redis
import functools

from smart.utils.serialize import TypeObjSerializer
from smart.utils.number import safe_parse_int
from .__utils import logger
from .redis_utils import RedisFullUtil, RedisLongPoll


class RedisQueue:
    def __init__(self, host='localhost', port:int=6379, db:int=0, 
                password:str=None, redis_kwargs:dict=None) -> None:
        other_args = redis_kwargs or {}
        redis = Redis(host=host, port=port, db=db, password=password, **other_args)
        self._redis = redis

    def __parse_key_item(self, key_item, key_item_redis=None, raw_item=False):
        if key_item is None:
            return None
        
        key, item_data = key_item

        type, item = TypeObjSerializer.decode(item_data)

        if raw_item:
            return type, item

        key = key.decode('utf8')
        # 将 redis key 加入item
        if isinstance(item, dict):
            if key_item_redis:
                item[key_item_redis] = key
            else:
                item = (item, key)

            return type, item
        else:
            return type, (item, key)
    
    def recv_one(self, key, timeout=0, key_item_redis='_redis_key', redis_poll_interval:int=None):
        """从redis队列接收一条数据

        Args:
            key (str|list): 队列的键; 数组表示多队列接收任务.
            timeout (int, optional): 空队列时等待时间, 单位为秒. Defaults to 0.
            key_item_redis (str, optional): 多队列接收任务时, 将具体到数据的队列的键写入item. Defaults to '_redis_key'.
            redis_poll_interval (int, optional): 缺省None, >0时启用redis长轮询机制获取数据. 建议设置redis长轮询间隔时间为10(秒). 

        Returns:
            tuple: type, item
        """
        redis = self._redis
        if redis_poll_interval:
            # 启用长轮询机制获取数据
            _redis_long_poll = RedisLongPoll(redis, poll_interval=redis_poll_interval)
            key_item = _redis_long_poll.blpop(key, timeout)
        else:
            key_item = redis.blpop(key, timeout)

        if key_item:
            is_multi_queue = isinstance(key, (list, tuple))
            if is_multi_queue:
                type, item = self.__parse_key_item(key_item, key_item_redis=key_item_redis)
            else:
                type, item = self.__parse_key_item(key_item, raw_item=True)

            return type, item
        else:
            return None, None

    def recv_all(self, key, block=True, timeout=0, key_item_redis='_redis_key'
            , is_daemon:bool=False, redis_poll_interval:int=None):
        """接收redis管道数据

        key为数组时, 将优先取第一个元素的队列; 如第一个队列无数据, 取第二个队列, 依次类推.

        守护任务将忽略end命令, 只响应exit命令; 普通任务可被end/exit命令关闭.

        Args:
            key (str|list, optional): 队列的键; 数组表示多队列接收任务. Defaults to None.
            block (bool, optional): 空队列时是否阻塞请求. Defaults to True.
            timeout (int, optional): 空队列时等待时间, 单位为秒. Defaults to 0.
            key_item_redis (str, optional): 多队列接收任务时, 将具体到数据的队列的键写入item. Defaults to '_redis_key'.
            is_daemon (bool, optional): 是否为守护任务. Defaults to False.
            redis_poll_interval (int, optional): 缺省None，>0时启用redis长轮询机制获取数据. 本参数仅在block=True时有效, 建议设置redis长轮询间隔时间为10(秒). 

        Yields:
            dict: Item
        """
        tuple_rst = False
        assert key
        redis = self._redis

        if isinstance(key, (list, tuple)) and not block:
            # multi key must set block=True
            block = True
            logger.warning('RedisQueue multi key mode only support block=True')
        
        logger.info('RedisQueue start recv %s %s', key, (block, timeout))

        if not block:
            recv_fn = redis.lpop
        else:
            if redis_poll_interval:
                # 启用长轮询机制获取数据
                _redis_long_poll = RedisLongPoll(redis, poll_interval=redis_poll_interval)
                recv_fn = lambda key: _redis_long_poll.blpop(key, timeout)
            else:
                recv_fn = lambda key: redis.blpop(key, timeout)
            tuple_rst = True
        
        is_multi_queue = isinstance(key, (list, tuple))
        
        if is_multi_queue:
            loads_fn = functools.partial(self.__parse_key_item, key_item_redis=key_item_redis)
            key = list(key)
        elif tuple_rst:
            loads_fn = functools.partial(self.__parse_key_item, raw_item=True)
        else:
            loads_fn = TypeObjSerializer.decode

        while True:
            item_str = recv_fn(key)

            if item_str:
                type, item = loads_fn(item_str)

                if type == 'cmd':
                    item = item or {}
                    qu_key = None

                    if is_multi_queue:
                        if not key_item_redis:
                            item, qu_key = item
                        else:
                            qu_key = item.get(key_item_redis)
                    
                    cmd_type = item.get('type')

                    if is_daemon:
                        end_types = ('exit',)
                    else:
                        end_types = ('end', 'exit')
                    
                    if cmd_type in end_types:
                        logger.debug('RedisQueue.recv %s cmd: %s', cmd_type, item)

                        end_ttl = item.get('forward')

                        if end_ttl:
                            cmd_str = TypeObjSerializer.encode(item, type)
                            redis.rpush(key, cmd_str)
                            redis.expire(key, end_ttl)
                            logger.debug('RedisQueue.recv forward end cmd: %s', item)
                        
                        if cmd_type in ('exit',):
                            break
                        else:
                            if is_multi_queue:
                                if qu_key in key:
                                    key.remove(qu_key)
                                
                                if len(key):
                                    continue
                                else:
                                    break
                            else:
                                break
                    
                    logger.debug('RedisQueue.recv cmd: %s', item)
                    continue

                yield item
            else:
                break
    
    def send_one(self, item, key=None, item_queue_key=None, queue_ttl:int=None):
        queue_key = item.pop(item_queue_key, key) if item_queue_key else key
        assert queue_key
        item_str = TypeObjSerializer.encode(item)
        self._redis.rpush(queue_key, item_str)
        if queue_ttl:
            self._redis.expire(queue_key, queue_ttl)

    def send_all(self, item_iter, key=None, item_queue_key=None, send_end_cmd=True, 
            end_ttl:int=None, empty_old:bool=False, max_queue_size:int=None, check_queue_step:int=None, 
            client_timeout:int=None, queue_ttl:int=None, item_resp_ttl_key=None):
        """向redis管道发送数据

        当目标队列存在多个接收任务时, 需设置 end_ttl

        Arguments:
            item_iter {iter} -- 数据生成器 (default: {None})

        Keyword Arguments:
            key {str} -- 存储数据的键 (default: {None})
            item_queue_key {str} -- 动态队列 (default: {None})
            send_end_cmd {bool} -- 是否向管道发送结束命令 (default: {True})
            end_ttl {int} -- 结束时是否设置存活时间 (default: {None})
            empty_old {bool} -- 启动时是否清空旧数据 (default: {False})
            max_queue_size {int} -- 队列最大积压数据量 (default: {None})
            check_queue_step {int} -- 每隔多少数据检查一次队列积压, 缺省 max_queue_size/10 (default: {None})
            client_timeout {int} -- 接收数据方读取数据timeout, 超时未拉取数据将回收资源
            queue_ttl {int} -- 设置队列的ttl (default: {None})
            item_resp_ttl_key {str} -- Item设置响应数据的TTL (default: {None})
        """
        count = 0
        end_msg = None
        stop_early = False
        redis = self._redis

        if end_ttl is None and client_timeout:
            # 服务端send数据完成后, redis资源释放保护
            end_ttl = max(172800, client_timeout)

        logger.info('RedisQueue start send %s, dyn_queue=%s, arg=%s', key, item_queue_key, (empty_old, max_queue_size))

        if empty_old:
            redis.delete(key)
        else:
            redis.persist(key)

        if max_queue_size:
            if not check_queue_step:
                check_queue_step = int(max_queue_size/10) or 1

        for i, item in enumerate(item_iter):
            if isinstance(item, dict):
                queue_key = item.pop(item_queue_key, key) if item_queue_key else key
                if item_resp_ttl_key: 
                    item_resp_ttl = item.pop(item_resp_ttl_key, None)
                    if item_resp_ttl is None:
                        item_resp_ttl = queue_ttl
                    item_resp_ttl = safe_parse_int(item_resp_ttl)
                else:
                    item_resp_ttl = queue_ttl
            else:
                queue_key = key
                item_resp_ttl = queue_ttl

            if not queue_key:
                logger.warning('RedisQueue can not send item: %s', item)
                continue

            if max_queue_size:
                if (i+1) % check_queue_step == 0:

                    fullUtil = RedisFullUtil(redis, queue_key=queue_key)

                    continue_task = fullUtil.wait_no_full(max_queue_size=max_queue_size, client_timeout=client_timeout)

                    if not continue_task:
                        end_msg = fullUtil.end_msg
                        stop_early = fullUtil.stop_early
            
            if stop_early:
                break

            item_str = TypeObjSerializer.encode(item)
            redis.rpush(queue_key, item_str)
            if item_resp_ttl:
                redis.expire(queue_key, item_resp_ttl)
            count += 1
        
        if send_end_cmd:
            cmd_data = {'type':'end'}

            if end_msg:
                cmd_data['msg'] = end_msg

            if end_ttl:
                cmd_data['forward'] = int(end_ttl)
                redis.expire(key, end_ttl)

            cmd_str = TypeObjSerializer.encode(cmd_data, 'cmd')
            redis.rpush(key, cmd_str)

        logger.info('RedisQueue.send %s items', count)
    
    def send_exit_cmd(self, key, end_ttl:int=None):
        """向redis队列发送离开命令, 用于daemon类型的接收队列任务.

        当目标队列存在多个接收任务时, 需设置 end_ttl

        Args:
            key (str, optional): 目标队列. Defaults to None.
            end_ttl (int, optional): 是否设置队列存活时间. Defaults to None.
        """
        cmd_data = {'type':'exit'}

        if end_ttl:
            cmd_data['forward'] = int(end_ttl)
            self._redis.expire(key, end_ttl)
        
        cmd_str = TypeObjSerializer.encode(cmd_data, 'cmd')
        self._redis.rpush(key, cmd_str)