from .bound import BoundFn, _set_real_func
from .__logger import logger_utils
import time


class RetryException(Exception):
    pass


class RetryFn(BoundFn):
    def __init__(self, func:callable, retry_limit:int=2, sleep_interval:int=None):
        BoundFn.__init__(self, func)
        self.__retry_limit = retry_limit
        self.__sleep_interval = sleep_interval

    def __call__(self, *args, **kwargs):
        for retry_no in range(self.__retry_limit):
            try:
                return BoundFn.__call__(self, *args, **kwargs)
            except Exception as e:
                logger_utils.warning("RetryFn call {} error, retry {}/{}".format(self.__name__, retry_no, self.__retry_limit))
                logger_utils.warning("args={} kwargs={}".format(args,kwargs))
                logger_utils.exception(e)
                if self.__sleep_interval and retry_no<self.__retry_limit-1:
                    logger_utils.warning("RetryFn call {}, wait {}s".format(self.__name__, self.__sleep_interval))
                    time.sleep(self.__sleep_interval)
        
        raise RetryException("RetryFn Failed to call {} {} times".format(self.__name__, self.__retry_limit))


def retry_fn(retry_limit=2, sleep_interval=None):

    def _fn_call(func):

        fn = RetryFn(func, retry_limit=retry_limit, sleep_interval=sleep_interval)
        _set_real_func(fn, func)
        return fn

    return _fn_call
