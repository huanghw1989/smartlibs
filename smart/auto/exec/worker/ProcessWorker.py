import multiprocessing as mp
import os, signal

from . import BaseWorker
from smart.auto.__logger import logger


class ProcessWorker(BaseWorker):
    def __init__(self, target, args=(), kwargs=None, name=None) -> None:
        BaseWorker.__init__(self, target, args=args, kwargs=kwargs, name=name)
        self._process = mp.Process(
            target=self._func, 
            args=self._func_args, 
            kwargs=self._func_kwargs)
    
    def start(self):
        self._process.start()

    def join(self, timeout=None):
        self._process.join(timeout=timeout)
    
    def is_alive(self):
        return self._process.is_alive()

    @property
    def ident(self):
        return self._process.pid

    @property
    def exitcode(self):
        return self._process.exitcode

    def safeStop(self):
        pass

    def forceStop(self):
        if self.is_alive():
            os.kill(self._process.pid, signal.SIGINT)
        #     logger.debug("ProcessWorker.forceStop kill pid=%s", self._process.pid)
        # else:
        #     logger.debug("ProcessWorker pid=%s has stop", self._process.pid)