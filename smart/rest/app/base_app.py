from abc import ABC, abstractmethod

from .boot import Bootable
from .cron import Crond


class BaseApplication(Bootable):
    def __init__(self, **kwargs):
        self.crond = None
    
    def start_crond(self, run_in_process=None, run_in_thread=None):
        if not self.crond:
            self.crond = Crond()
        
        opts = self.boot_config.opts
        
        if run_in_process is None:
            run_in_process = opts.crond_run_in_process
        
        if run_in_thread is None:
            run_in_thread = not run_in_process

        return self.crond.daemon(run_in_process=run_in_process, run_in_thread=run_in_thread)
    
    def end_crond(self):
        if self.crond is not None:
            self.crond.close()


class BaseAppServer(ABC):
    @abstractmethod
    def start(self, app:BaseApplication):
        pass
    
    @abstractmethod
    def daemon(self):
        pass

    @abstractmethod
    def close(self):
        pass


class BaseWsgiServer(BaseAppServer):
    def daemon(self):
        return False

    @abstractmethod
    def wsgi(self, env:dict, start_response:callable):
        pass