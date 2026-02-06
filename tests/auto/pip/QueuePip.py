# python -m tests.auto.pip.QueuePip test_send_recv
### Test send timeout
# python -m tests.auto.pip.QueuePip test_send_recv --recv_interval=0.5 --send_timeout=0.4
### Test recv timeout
# python -m tests.auto.pip.QueuePip test_send_recv --send_interval=0.5 --recv_timeout=0.4 --recv_interval=0
import threading, time
from queue import Queue, Empty
from smart.auto.pip.QueuePip import *
from smart.auto.pip.cmd import end_cmd
from tests.auto import logger


def _pip_send_data(pip:QueuePip, num_item:int, send_block=True, send_timeout=None, send_interval:float=0.):
    try:
        for i in range(num_item):
            time.sleep(send_interval)
            logger.info("_pip_send_data send %d begin", i)
            ts_begin = time.time()
            pip.send(i, block=send_block, timeout=send_timeout)
            logger.info("_pip_send_data send %d end, cost %s seconds", i, time.time()-ts_begin)
    finally:
        pip.send(end_cmd)
        logger.info("_pip_send_data end")


def _pip_recv_data(pip:QueuePip, recv_interval:float=0.5, recv_block=True, 
            recv_timeout=None, recv_end_on_timeout=False):
    item_iter = pip.recv(
        block=recv_block, 
        timeout=recv_timeout,
        end_on_timeout=recv_end_on_timeout
    )

    ts_begin = time.time()
    for i, item in enumerate(item_iter):
        recv_during = time.time() - ts_begin
        logger.info("_pip_recv_data-%d: %s, cost %s seconds", i, item, recv_during)
        time.sleep(recv_interval)
        ts_begin = time.time()
    
    logger.info("_pip_recv_data end")


def test_send_recv(queue_max_size=3, num_item:int=10, 
        recv_interval:float=0.5, recv_block:bool=True, 
        recv_timeout:float=None, recv_end_on_timeout:bool=False,
        send_block:bool=True, send_timeout:float=None, send_interval:float=0.):
    pip = QueuePip(
        queue = Queue(maxsize=queue_max_size)
    )

    thread_send = threading.Thread(
        target = _pip_send_data,
        args = (pip, num_item),
        kwargs = {
            'send_block': send_block,
            'send_timeout': send_timeout,
            'send_interval': send_interval
        }
    )
    thread_recv = threading.Thread(
        target = _pip_recv_data,
        args = (pip,),
        kwargs = {
            'recv_interval': recv_interval,
            'recv_block': recv_block,
            'recv_timeout': recv_timeout,
            'recv_end_on_timeout': recv_end_on_timeout
        }
    )
    thread_send.start()
    thread_recv.start()

    thread_send.join()
    thread_recv.join()
    logger.info("test_send_recv ended")


def _pip_recv_data_timeout_fn(pip:QueuePip, recv_interval:float=0.5):
    item_no = 0
    def _recv_block_fn():
        return True

    def _recv_timeout_fn():
        timeout = 0.2 + 0.1 * item_no
        logger.info("_recv_timeout_fn: %s", timeout)
        return timeout
    
    begin_ts = time.time()
    while True:
        try:
            for i, item in enumerate(pip.recv(
                block_fn=_recv_block_fn, timeout_fn=_recv_timeout_fn, raise_empty=True
                )):
                item_no += 1
                logger.info("_pip_recv_data %d: %s, ts=%s", i, item, time.time() - begin_ts)
                begin_ts = time.time()
            break
        except Empty:
            logger.info("_pip_recv_data Empty")
            continue

def test_send_recv_timeout_fn(queue_max_size=3, num_item:int=10, 
        recv_interval:float=0.5, send_block:bool=True, send_timeout:float=None):
    pip = QueuePip(
        queue = Queue(maxsize=queue_max_size)
    )
    thread_send = threading.Thread(
        target = _pip_send_data,
        args = (pip, num_item),
        kwargs = {
            'send_block': send_block,
            'send_timeout': send_timeout,
            'send_interval': 0.5
        }
    )
    thread_recv = threading.Thread(
        target = _pip_recv_data_timeout_fn,
        args = (pip,),
        kwargs = {
            'recv_interval': recv_interval
        }
    )
    thread_send.start()
    thread_recv.start()

    thread_send.join()
    thread_recv.join()
    logger.info("test_send_recv ended")



if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)