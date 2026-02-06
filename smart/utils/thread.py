from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError

from .__logger import logger_utils
from .bound import BoundFn


class BoundTask(BoundFn):
    def __init__(self, fn:callable):
        super().__init__(fn)
        self.__done = False
    
    def __call__(self, *args, **kwargs):
        try:
            return self.__func__(*args, **kwargs)
        finally:
            self.__done = True
    
    def done(self):
        return self.__done


class ThreadManage:
    def __init__(self, executor:ThreadPoolExecutor):
        self.executor = executor
        self.__all_future = set()
    
    @staticmethod
    def pool_executor(max_workers=None, thread_name_prefix='', **kwargs):
        executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=thread_name_prefix, **kwargs)

        return ThreadManage(executor)

    def submit(self, fn, *args, **kwargs):
        fn = BoundTask(fn)
        future = self.executor.submit(fn, *args, **kwargs)
        future.bound_task = fn

        self.__all_future.add(future)

        return future
    
    def wait(self, futures:list=None, check_interval=3):
        if futures is None:
            futures = list(self.__all_future)

        for future in futures:
            future:Future
            bound_task:BoundTask = getattr(future, 'bound_task', None)

            if bound_task is not None and isinstance(bound_task, BoundTask):

                while True:
                    try:
                        future.result(check_interval)
                        break
                    except TimeoutError:

                        if bound_task.done():
                            logger_utils.debug('future is done: %s', bound_task.__func__)
                            if not future.done():
                                future.cancel()
                            break
                        
                if future in self.__all_future:
                    self.__all_future.remove(future)
            else:

                future.result()