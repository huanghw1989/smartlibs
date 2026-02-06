import threading
from . import BaseWorker
from smart.auto.__logger import logger

class ThreadWorker(BaseWorker):
    def __init__(self, target, args=(), kwargs=None, name=None) -> None:
        BaseWorker.__init__(self, target, args=args, kwargs=kwargs, name=name)
        self._thread = threading.Thread(
            target=self._func, 
            args=self._func_args, 
            kwargs=self._func_kwargs)

    def start(self):
        self._thread.start()
        logger.debug('ThreadWorker %s started', self.ident)

    def join(self, timeout=None):
        self._thread.join(timeout=timeout)

    def is_alive(self):
        return self._thread.is_alive()

    @property
    def ident(self):
        return self._thread.ident

    def safeStop(self):
        pass

    def forceStop(self):
        pass