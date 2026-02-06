import multiprocessing as mp
import time
import threading
import logging

from smart.utils.store.store import ContextStore

from smart.rest import BootConfig
from smart.rest.aio.application import AsyncServiceApplication
from smart.rest.aio.queue_handler import QueueAsyncRequestHandler


boot = BootConfig()


@boot.crond()
@boot.service('app.*')
class TestAioApp(AsyncServiceApplication):
    pass


def test_run(n=5, resp_timeout=10):
    # mp.set_start_method('spawn', True)

    context = ContextStore() # For Debug
    # context = None
    
    req_queue = mp.Queue()
    out_queue = mp.Queue()

    handler = QueueAsyncRequestHandler(out_queue)
    app = TestAioApp(req_queue, handler, context=context)

    app_thread = threading.Thread(target=app.daemon)
    app_thread.start()

    for i in range(n):
        req_data = {
            'req_id': 'auto_'+str(i+1),
            'path': '/test/sleep',
            'query': {
                'interval': 3
            }
        }
        req_queue.put(req_data)
    
    print('sended {} requests'.format(n))
    
    for i in range(n):
        try:
            resp_data = out_queue.get(True, resp_timeout or None)
            print('resp {}:'.format(i), resp_data)
        except BaseException as e:
            print('fail get response:', type(e), e)
            break
    
    app.close()
    app_thread.join()


def test_stress(n=500, sleep_interval=.001, worker_num=10, resp_timeout=10):
    # mp.set_start_method('spawn', True)
    logging.getLogger('rest').setLevel(logging.INFO)

    print('stress test:', {
        'n': n,
        'sleep_interval': sleep_interval,
        'worker_num': worker_num
    })

    context = ContextStore() # For Debug
    # context = None
    
    req_queue = mp.Queue()
    out_queue = mp.Queue()

    handler = QueueAsyncRequestHandler(out_queue)
    app = TestAioApp(req_queue, handler, context=context, worker_num=worker_num)

    app_thread = threading.Thread(target=app.daemon)
    app_thread.start()

    ts_start = time.time()

    for i in range(n):
        req_data = {
            'req_id': 'auto_'+str(i+1),
            'path': '/test/sleep',
            'query': {
                'interval': sleep_interval
            }
        }
        req_queue.put(req_data)
    
    ts_end_send = time.time()
    
    print('sended {} requests tooks {} seconds'.format(n, ts_end_send-ts_start))
    
    for i in range(n):
        try:
            resp_data = out_queue.get(True, resp_timeout or None)
            # print('resp {}:'.format(i), resp_data)
        except BaseException as e:
            print('fail get response:', type(e), e)
            break
    
    ts_end = time.time()
    print('handle {} requests tooks {} seconds'.format(n, ts_end-ts_start))
    
    app.close()
    app_thread.join()


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)