# python -m tests.utils.batch.BatchItemRecv test_batch_item_recv
# python -m tests.utils.batch.BatchItemRecv test_batch_item_recv --batch_size=3 --send_interval=0.1 --send_interval_inc=0.05 --recv_timeout=None
# python -m tests.utils.batch.BatchItemRecv test_batch_item_recv --batch_size=3 --send_interval=0 --send_interval_inc=0 --recv_timeout=None
import time
import threading
from queue import Queue, Empty
from smart.utils.common.value import is_null
from smart.utils.batch.ItemRecv import QueueItemRecv
from smart.utils.batch.BatchItemRecv import *
from tests.utils import logger


def _queue_put_data(queue:Queue, num_item, interval:float=0., interval_inc:float=0.):
    logger.info("_queue_put_data begin")
    for i in range(num_item):
        time.sleep(interval + interval_inc * i)
        queue.put({
            "id": i,
            "ts": time.time()
        })
        logger.info("_queue_put_data item %s", i)
    queue.put(None)


def test_batch_item_recv(batch_size:int=2, num_item:int=10, 
            recv_block:bool=True, recv_timeout:float=0.5, recv_batch_timeout:float=0.8,
            send_interval:float=0.2, send_interval_inc:float=0.1):
    logger.info("test_batch_item_recv BEGIN")
    _queue = Queue()
    item_recv = QueueItemRecv(
        _queue,
        is_end_fn = is_null
    )

    thread_send = threading.Thread(
        target=_queue_put_data, 
        args=(_queue, num_item),
        kwargs= {
            "interval": send_interval,
            "interval_inc": send_interval_inc
        }
    )
    thread_send.start()

    batch_item_recv = BatchItemRecv(item_recv)

    batch_iter = batch_item_recv.iter_fn(
        batch_size=batch_size,
        block=recv_block,
        timeout=recv_timeout,
        batch_timeout=recv_batch_timeout
    )

    begin_ts = time.time()
    for batch_no, batch_item in enumerate(batch_iter):
        during = time.time() - begin_ts
        begin_ts = time.time()
        if len(batch_item):
            batch_delay = time.time() - batch_item[0]['ts']
        else:
            batch_delay = None
        logger.info("test_batch_item_recv-%s item=%s, cost %s seconds, batch_delay=%s", batch_no, batch_item, during, batch_delay)
    
    logger.info("test_batch_item_recv END")


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)