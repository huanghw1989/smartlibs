import time, sys

from smart.auto.exec.worker.ThreadWorker import *
from tests.auto import logger

def foo(n=10, sleep=1.0):
    logger.info("Start foo sleepInterval=%s, n=%s", sleep, n)

    for i in range(n):
        time.sleep(sleep)
        logger.info("foo sleep i=%s", i)

def test_thread(n=10, sleep=1.0, joinTimeout=2):
    worker = ThreadWorker(foo, kwargs={
        'n': n,
        'sleep': sleep
    })

    logger.info("worker(before start) ident: %s, is_alive: %s", worker.ident, worker.is_alive())

    worker.start()

    logger.info("worker(after start) ident: %s, is_alive: %s", worker.ident, worker.is_alive())

    for i in range(sys.maxsize):
        worker.join(joinTimeout)
        logger.info("worker(after join %s) ident: %s, is_alive: %s", i, worker.ident, worker.is_alive())

        if not worker.is_alive():
            break
    
    logger.info('test_thread end')
    


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)