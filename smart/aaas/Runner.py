import multiprocessing as mp
from queue import Empty
import threading, time

from smart.rest import RestServiceApplication, BootConfig

from smart.aaas.auto_manage import AutoManage

from smart.aaas.__logger import logger


boot = BootConfig()


# @boot.crond(run_in_process=True)
@boot.crond()
@boot.service('service.*')
class ServiceRunner(RestServiceApplication):
    def __init__(self, **kwargs):
        self.auto_manage = AutoManage()
        self.auto_manage.start()

        RestServiceApplication.__init__(self, **kwargs)
    
    def _listen_shut_sig(self):
        _sig_shut = getattr(self, '__sig_shut__', None)

        if _sig_shut is None:
            logger.warning('exit listen_shut_sig because of missing __sig_shut__')
            return 

        while True:
            try:
                _sig = _sig_shut.get(True, 1)

                if _sig == 'shut_down_app':
                    self.shutdown()
                    break
            except Empty:
                if self._status == 'close':
                    break
    
    def enable_remote_shuttable(self):
        if getattr(self, '__sig_shut__', None) is None:
            self.__sig_shut__ = mp.Queue()

        self._thread_shut_sig = threading.Thread(target=self._listen_shut_sig)
        self._thread_shut_sig.start()