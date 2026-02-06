# python -m tests.utils.batch.ItemRecv test_queue_item_recv_iter_fn
import time
import threading

from smart.utils.batch.ItemRecv import *
from tests.utils import logger


def _queue_put_data(queue:Queue, num_item, interval:float=0., interval_inc:float=0.):
    logger.info("_queue_put_data begin")
    for i in range(num_item):
        time.sleep(interval + interval_inc * i)
        queue.put(i)
        logger.info("_queue_put_data item %s", i)


def test_queue_item_recv_iter_fn(num_item:int=10, recv_timeout:float=0.5,
        send_interval:float=0.2, send_interval_inc:float=0.1):
    _queue = Queue()
    item_recv = QueueItemRecv(_queue)

    thread_send = threading.Thread(
        target=_queue_put_data, 
        args=(_queue, num_item),
        kwargs= {
            "interval": send_interval,
            "interval_inc": send_interval_inc
        }
    )
    thread_send.start()
    
    _item_iter = item_recv.iter_fn(
        block=True, timeout=recv_timeout, raise_empty=False
    )
    
    item_count, last_item_ts = 0, time.time()
    for i, item in enumerate(_item_iter):
        if item is not None:
            item_count += 1
            recv_during = time.time() - last_item_ts
            last_item_ts = time.time()
        else:
            recv_during = None
        logger.info("item_recv %s, i=%s, item_count=%s, during=%s", item, i, item_count, recv_during)
        if item_count>=num_item:
            break
    
    logger.info("test_queue_item_recv_iter_fn done")


if __name__ == "__main__":
    import fire
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })