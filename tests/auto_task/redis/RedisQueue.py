'''
启动本地测试的redis服务: docker run -d --name myredis -p 6379:6379 redis redis-server --appendonly yes
python -m tests.auto_task.redis.RedisQueue test_send_recv
python -m tests.auto_task.redis.RedisQueue test_send_recv_all
'''
import time, uuid
from auto_tasks.redis.RedisQueue import RedisQueue
from tests.auto_task import logger


def test_send_recv(n:int=2, key='test_key', host='127.0.0.1', port:int=6379, db:int=0, password=None):
    redis_queue = RedisQueue(
        host=host,
        port=port,
        db=0,
        password=password
    )

    for i in range(n):
        item = {
            "idx": i,
            "ts": time.time()
        }
        redis_queue.send_one(item, key=key)
        logger.info("send-%s %s", i, item)
    redis_queue.send_exit_cmd(key)
    
    while True:
        type, item = redis_queue.recv_one(
            key,
            timeout=60,
            redis_poll_interval=10
        )
        logger.info("recv type=%s, item=%s", type, item)
        if type is None and item is None:
            logger.warning("recv_one timeout")
        if type == 'cmd':
            item = item or {}
            cmd_type = item.get('type')
            if cmd_type in ('end', 'exit'):
                break
    logger.info("test_send_recv done")


def _item_iter_fn(n, **kwargs):
    for i in range(n):
        item = {
            "idx": i,
            "ts": time.time()
        }
        item.update(kwargs)
        yield item

def test_send_recv_all(n:int=2, key='test_key', host='127.0.0.1', port:int=6379, db:int=0, password=None):
    req_key = key+':'+uuid.uuid1().hex

    redis_queue = RedisQueue(
        host=host,
        port=port,
        db=0,
        password=password
    )
    send_item_iter = _item_iter_fn(
        n,
        _req_queue=req_key # 指定动态请求队列
    )

    redis_queue.send_all(
        send_item_iter,
        key=key,
        item_queue_key='_req_queue', # 动态请求队列
        send_end_cmd=True
    )
    dyn_recv_item_iter = redis_queue.recv_all(
        req_key,
        timeout=60,
        redis_poll_interval=10
    )
    recv_item_iter = redis_queue.recv_all(
        key,
        timeout=60,
        redis_poll_interval=10
    )
    dyn_recv_count, recv_count = 0, 0
    for i, item in enumerate(dyn_recv_item_iter):
        dyn_recv_count += 1
        logger.info("recv-%s %s", i, item)
        if dyn_recv_count >= n:
            break
    for i, item in enumerate(recv_item_iter):
        recv_count += 1
        logger.info("recv-%s %s", i, item)
    assert dyn_recv_count == n
    assert recv_count == 0


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)