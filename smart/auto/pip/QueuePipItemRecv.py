from queue import Empty
from smart.utils.batch.ItemRecv import BaseItemRecv
from .QueuePip import QueuePip
from .event import TimeoutEvent


class QueuePipItemRecv(BaseItemRecv):
    def __init__(self, pip:QueuePip) -> None:
        self._pip = pip
        self.__isEnded = False

        self._timeout = None
        self._block = None

        self._item_iter = pip.recv(
            block_fn = self._block_fn,
            timeout_fn = self._timeout_fn,
            raise_empty=False,
            end_on_timeout = False,
            on_timeout = self._on_timeout
        )
    
    def _on_timeout(self):
        return TimeoutEvent()

    def _block_fn(self):
        return self._block
    
    def _timeout_fn(self):
        return self._timeout
    
    def recv(self, block: bool = True, timeout: float = None):
        self._block = block
        self._timeout = timeout
        try:
            item = next(self._item_iter)
            if isinstance(item, TimeoutEvent):
                raise Empty()
            return item
        except StopIteration:
            self.__isEnded = self._pip.is_ended
            raise Empty()

    def isEnded(self):
        return self.__isEnded