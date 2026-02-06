from ..base import BasePip
from .QueuePip import QueuePip

from ..__logger import logger


class Broadcast(BasePip):
    """1对多的广播管道
    """
    DEBUG_MODE = False
    default_pip_fn = lambda *args:QueuePip()

    def __init__(self, pip_fn:callable=None):
        """构造函数

        Keyword Arguments:
            pip_fn {callable} -- 缺省值None将自动替换为lambda:QueuePip() (default: {None})
        """
        self.pip_fn = pip_fn if pip_fn else self.default_pip_fn
        self.pips = []
        self.pip_debug = self.create_pip() if self.DEBUG_MODE else None

    def create_pip(self):
        new_pip = self.pip_fn()
        self.pips.append(new_pip)
        return new_pip

    def send(self, data, *args, **kwargs):
        for pip in self.pips:
            pip.send(data, *args, **kwargs)

    def recv(self, *args, **kwargs):
        if self.DEBUG_MODE and self.pip_debug:
            for item in self.pip_debug.recv(*args, **kwargs):
                yield item
            # yield from self.pip_debug.recv(*args, **kwargs)
            return
        logger.warning('Broadcast always recv no data')
        yield from []
    
    # def close(self):
    #     for pip in self.pips:
    #         pip.close()