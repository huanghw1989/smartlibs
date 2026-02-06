from redis import Redis
import time

from .__utils import logger
from smart.auto.__logger import logger_trace


class RedisFullUtil:
    def __init__(self, redis:Redis, queue_key):
        self._redis = redis
        self.queue_key = queue_key
        self.end_msg = None
        self.stop_early = False
    
    def wait_no_full(self, max_queue_size:int, client_timeout:int=None, sleep_interval:int=5) -> bool:
        """等待redis队列未满

        Args:
            max_queue_size (int): 最大队列长度
            client_timeout (int, optional): 接收数据方读取数据timeout(单位: 秒), 超时未拉取数据将回收资源. Defaults to None.
            sleep_interval (int, optional): sleep间隔时间(单位: 秒). Defaults to 5.

        Returns:
            bool: True可以继续执行任务, False表示应退出任务(如超时)
        """
        redis = self._redis
        queue_key = self.queue_key
        queue_len = redis.llen(queue_key)

        prev_queue_len = None
        client_last_recv_ts = None
        client_no_recv_during = None

        while True:
            queue_len = redis.llen(queue_key)

            if queue_len > max_queue_size:
                if queue_len == prev_queue_len:
                    if client_last_recv_ts is None:
                        client_last_recv_ts = time.time() - sleep_interval
                        client_no_recv_during = sleep_interval
                    else:
                        client_no_recv_during = time.time() - client_last_recv_ts
                else:
                    client_last_recv_ts = None
                    client_no_recv_during = None

                logger.info("RedisPip key %s length is %d, max_queue_size is %d, client_last_recv_ts=%s, client_no_recv_during=%s, please wait"
                    , queue_key, queue_len, max_queue_size, client_last_recv_ts, client_no_recv_during)

                if client_timeout and client_no_recv_during:
                    # 客户端超时保护
                    if client_no_recv_during >= client_timeout:
                        self.end_msg = "client timeout({}s)".format(client_timeout)
                        self.stop_early = True
                        logger.info("RedisPip key %s stop early because of client_timeout", queue_key)
                        return False

                time.sleep(sleep_interval)
                prev_queue_len = queue_len
                continue

            return True
    

class RedisLongPoll:
    def __init__(self, redis:Redis, poll_interval:int=10):
        self.__redis = redis
        if poll_interval < 1:
            raise Exception("poll_interval must >=1")

        self.__poll_interval = poll_interval
    
    def blpop(self, key, timeout=0):
        rest_time = timeout if timeout > 0 else 888
        while True:
            if timeout > 0:
                _timeout_this_turn = min(rest_time, self.__poll_interval)
                rest_time -= _timeout_this_turn
            else:
                _timeout_this_turn = self.__poll_interval
            
            item_str = self.__redis.blpop(key, _timeout_this_turn)
            if item_str is not None:
                return item_str
            
            if rest_time <= 0:
                return None
            
            logger_trace.debug("RedisLongPoll.blpop %s rest_time=%s", key, rest_time)