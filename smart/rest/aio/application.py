from queue import Queue, Empty
from concurrent.futures.thread import ThreadPoolExecutor
import functools

from smart.utils.store.mp_store import MpContextStore

from ..app.base_app import BaseApplication
from ..app.dispatch import ServiceDispatcher
from .handler import BaseAsyncRequestHandler
from .request import AsyncReqData, AsyncRequest

from ..__logger import logger_rest


class AsyncServiceApplication(BaseApplication):
    def __init__(self, req_queue:Queue, handler:BaseAsyncRequestHandler, worker_num=2, req_fn=None, context=None, **kwargs):
        super().__init__(**kwargs)

        self._req_queue = req_queue
        self._handler = handler
        self._opts = kwargs
        self._req_fn = req_fn
        self._worker_num = worker_num

        self._pool = None
        self.ctx = MpContextStore() if context is None else context
        self.dispatcher = ServiceDispatcher(self)
        self.ctx.dict('app_status')['stage'] = 'init'
    
    @property
    def worker_pool(self):
        if self._pool is None:
            self._pool = ThreadPoolExecutor(max_workers=self._worker_num)
        
        return self._pool

    def do_req(self, req_data, req_fn=None):
        a_req_data = None

        if req_fn:
            req_data = req_fn(req_data)

        if isinstance(req_data, dict):
            a_req_data = AsyncReqData(**req_data)
        elif isinstance(req_data, AsyncReqData):
            a_req_data = req_data
        
        if a_req_data is None:
            logger_rest.debug('AsyncServiceApplication empty req_data')
            return
        
        a_req = AsyncRequest(req_data=a_req_data, handler=self._handler)
        http_method = a_req.command

        self.dispatcher.dispatch(http_method, a_req)
    
    def start_worker(self):
        _q = self._req_queue
        _req_fn = self._req_fn
        worker_pool = self.worker_pool
        ctx = self.ctx.dict('app_status')

        if not callable(_req_fn):
            _req_fn = None
        
        self.ctx.dict('app_status')['stage'] = 'start'

        while not ctx.get('stop_flag'):
            data = None

            try:
                data = _q.get(block=True, timeout=5)
            except Empty:
                continue
            except KeyboardInterrupt:
                break

            try:
                # self.do_req(data, req_fn=_req_fn)
                worker_pool.submit(functools.partial(self.do_req, data, req_fn=_req_fn))
            except KeyboardInterrupt:
                break
            except BaseException as e:
                logger_rest.exception('AsyncServiceApplication process error')
                continue
    
    def __start_app(self):
        boot_config = self.boot_config

        if boot_config == None:
            logger_rest.error('miss boot config')
        
        boot_config.init()

        if boot_config.opts.crond_enable:
            self.start_crond()
        
        self.start_worker()
    
    def daemon(self):
        try:

            self.__start_app()
        except KeyboardInterrupt:

            logger_rest.info('End AsyncServiceApplication (KeyboardInterrupt)')
        else:

            logger_rest.info('End AsyncServiceApplication')
        finally:

            self.close()

    def shutdown(self):
        self.close()
    
    def close(self):
        self.ctx.dict('app_status').update({
            'stop_flag': 1,
            'stage': 'close'
        })
        self.end_crond()

    def __getstate__(self):
        """spawn 模式的多进程会使用 pickle 序列化本实例
        """
        _dict = self.__dict__.copy()
        _dict.update(
            _req_queue = None,
            _pool = None
        )
        return _dict

    def __setstate__(self, state):
        """pickle 反序列化
        """
        self.__dict__.update(state)




    
