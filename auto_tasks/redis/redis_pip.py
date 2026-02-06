from redis import Redis
import redis as _redis
import functools

from smart.utils.serialize import TypeObjSerializer
from smart.utils.common.cluster import parse_nodes_host
from smart.utils.number import safe_parse_int
from smart.auto.tree import TreeMultiTask

from .__utils import auto_load, logger
from .redis_utils import RedisFullUtil, RedisLongPoll


@auto_load.task('redis__pip')
class RedisPipTask(TreeMultiTask):

    def conn(self, host='localhost', port:int=6379, db:int=0, password:str=None, use_cluster:bool=False, redis_kwargs:dict=None):
        """初始化redis连接

        Args:
            host (str, optional): redis服务域名或IP. Defaults to 'localhost'.
            port (int, optional): redis服务端口. Defaults to 6379.
            db (int, optional): redis db. Defaults to 0.
            password (str, optional): redis连接密码. Defaults to None.
            use_cluster (bool, optional): 是否使用redis集群. Defaults to False.
            redis_kwargs (dict, optional): Redis对象初始化的其他参数. Defaults to None.

        Returns:
            dict: {redis:Redis}
        """
        other_args = redis_kwargs or {}
        passwd_log = 'auth **' if password else 'no password'
        if use_cluster:
            # redis cluster不支持选择db
            default_port = port or 6379
            host_port_list = parse_nodes_host(host, default_port=default_port)
            assert len(host_port_list)
            logger.debug('redis__pip.conn cluster=%s, %s, opts=%s', host_port_list, passwd_log, redis_kwargs)
            nodes = [
                _redis.cluster.ClusterNode(host=host, port=port)
                for host, port in host_port_list
            ]
            redis = _redis.cluster.RedisCluster(
                startup_nodes=nodes, password=password, **other_args)
        else:
            logger.debug('redis__pip.conn %s:%s:%s, %s, opts=%s', host, port, db, passwd_log, redis_kwargs)
            redis = _redis.Redis(host=host, port=port, db=db, password=password, **other_args)

        return {
            'redis': redis
        }
    
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
    
    def recv(self, redis:Redis, key=None, block=True, timeout=0, key_item_redis='_redis_key'
            , is_daemon:bool=False, redis_poll_interval:int=None):
        """接收redis管道数据

        key为数组时, 将优先取第一个元素的队列; 如第一个队列无数据, 取第二个队列, 依次类推.

        守护任务将忽略end命令, 只响应exit命令; 普通任务可被end/exit命令关闭.

        Args:
            redis (Redis): redis客户端实例, 一般由前置调用的conn函数传参过来.
            key (str|list, optional): 队列的键; 数组表示多队列接收任务. Defaults to None.
            block (bool, optional): 空队列时是否阻塞请求. Defaults to True.
            timeout (int, optional): 空队列时等待时间, 单位为秒. Defaults to 0.
            key_item_redis (str, optional): 多队列接收任务时, 将具体到数据的队列的键写入item. Defaults to '_redis_key'.
            is_daemon (bool, optional): 是否为守护任务. Defaults to False.
            redis_poll_interval (int, optional): 缺省None，>0时启用redis长轮询机制获取数据. 本参数仅在block=True时有效, 建议设置redis长轮询间隔时间为10(秒). 

        Returns:
            dict: {item_iter_fn}
        """
        tuple_rst = False
        assert key

        if isinstance(key, (list, tuple)) and not block:
            # multi key must set block=True
            block = True
            logger.warning('RedisPip multi key mode only support block=True')
        
        logger.info('RedisPip start recv %s %s', key, (block, timeout))

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

        def item_iter_fn():
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
                            logger.debug('RedisPip.recv %s cmd: %s', cmd_type, item)

                            end_ttl = item.get('forward')

                            if end_ttl:
                                cmd_str = TypeObjSerializer.encode(item, type)
                                redis.rpush(key, cmd_str)
                                redis.expire(key, end_ttl)
                                logger.debug('RedisPip.recv forward end cmd: %s', item)
                            
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
                        
                        logger.debug('RedisPip.recv cmd: %s', item)
                        continue

                    yield item
                else:
                    break
        
        return {
            'item_iter_fn': item_iter_fn
        }

    def send(self, redis:Redis, key=None, item_queue_key=None, item_iter=None, item_iter_fn=None, recv_args={}, 
            send_end_cmd=True, end_ttl:int=None, empty_old:bool=False, max_queue_size:int=None, check_queue_step:int=None, 
            client_timeout:int=None, queue_ttl:int=None, item_resp_ttl_key=None):
        """向redis管道发送数据

        当目标队列存在多个接收任务时, 需设置 end_ttl

        Arguments:
            redis {Redis} -- redis客户端实例, 一般由前置调用的conn函数传参过来.

        Keyword Arguments:
            key {str} -- 存储数据的键 (default: {None})
            item_queue_key {str} -- 动态队列 (default: {None})
            item_resp_ttl_key {str} -- Item设置响应数据的TTL (default: {None})
            item_iter {iter} -- 数据生成器 (default: {None})
            item_iter_fn {callable} -- 数据生成器函数 (default: {None})
            recv_args {dict} -- 队列接收数据的参数 (default: {{}})
            send_end_cmd {bool} -- 是否向管道发送结束命令 (default: {True})
            end_ttl {int} -- 结束时是否设置存活时间 (default: {None})
            empty_old {bool} -- 启动时是否清空旧数据 (default: {False})
            max_queue_size {int} -- 队列最大积压数据量 (default: {None})
            check_queue_step {int} -- 每隔多少数据检查一次队列积压, 缺省 max_queue_size/10 (default: {None})
            client_timeout {int} -- 接收数据方读取数据timeout, 超时未拉取数据将回收资源
            queue_ttl {int} -- 设置队列的ttl (default: {None})
        """
        item_iter = item_iter or (item_iter_fn or self.recv_data)(**recv_args)
        count = 0
        end_msg = None
        stop_early = False

        if end_ttl is None and client_timeout:
            # 服务端send数据完成后, redis资源释放保护
            end_ttl = max(172800, client_timeout)

        logger.info('RedisPip start send %s, dyn_queue=%s, arg=%s', key, item_queue_key, (empty_old, max_queue_size))

        if key:
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
                logger.warning('RedisPip can not send item: %s', item)
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

        logger.info('redis__pip.send %s items', count)
    
    def send_exit_cmd(self, redis:Redis, key=None, end_ttl:int=None):
        """向redis队列发送离开命令, 用于daemon类型的接收队列任务.

        当目标队列存在多个接收任务时, 需设置 end_ttl

        Args:
            redis (Redis): redis客户端实例
            key (str, optional): 目标队列. Defaults to None.
            end_ttl (int, optional): 是否设置队列存活时间. Defaults to None.
        """
        assert key

        cmd_data = {'type':'exit'}

        if end_ttl:
            cmd_data['forward'] = int(end_ttl)
            redis.expire(key, end_ttl)
        
        cmd_str = TypeObjSerializer.encode(cmd_data, 'cmd')
        redis.rpush(key, cmd_str)

        logger.info('redis__pip.send_exit_cmd to queue %s', key)
