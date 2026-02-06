from queue import Empty, Queue
from smart.utils.common.value import alway_false
from smart.utils.__logger import logger_utils_trace


class BaseItemRecv:
    def recv(self, block:bool=True, timeout:float=None):
        """接受一条数据

        Args:
            block (bool, optional): 是否阻塞式获取数据; 当block=False时，无新数据时立即抛出Empty异常. Defaults to True.
            timeout (float, optional): 超时时间, 单位秒; 超出timeout秒后仍无新数据, 抛出Empty异常. Defaults to None.

        Raises:
            Empty: 暂时无新数据, 不代表没有更多数据

        Returns:
            Any: Item
        """
        if block:
            return None
        else:
            raise Empty()
    
    def isEnded(self) -> bool:
        """数据获取是否已经结束

        Returns:
            bool: True表示没有更多数据
        """
        return True
    
    def iter_fn(self, block:bool=True, timeout:float=None, 
            block_fn:callable=None, timeout_fn:callable=None, raise_empty:bool=True):
        """生成器方式获取数据

        Args:
            block (bool, optional): 是否阻塞式获取数据. Defaults to True.
            timeout (float, optional): 获取数据的超时时间, 单位秒. Defaults to None.
            block_fn (callable, optional): block值的回调函数; 当不为空时block参数失效. Defaults to None.
            timeout_fn (callable, optional): timeout值的回调函数; 当不为空时timeout参数失效. Defaults to None.
            raise_empty (bool, optional): 当无新数据时是否抛出Empty异常; False时, 无新数据则yield None. Defaults to True.

        Raises:
            Empty: 暂时无新数据, 不代表没有更多数据

        Yields:
            Any: recv函数返回的数据
        """

        while not self.isEnded():
            _block = block_fn() if block_fn else block
            _timeout = timeout_fn() if timeout_fn else timeout
            try:
                item = self.recv(block=_block, timeout=_timeout)
                yield item
            except Empty as e:
                if raise_empty:
                    raise e
                else:
                    yield None


class QueueItemRecv(BaseItemRecv):
    def __init__(self, queue: Queue, is_end_fn:callable=None) -> None:
        self.__isEnded = False
        self._queue = queue
        self._is_end_fn = is_end_fn or alway_false
    
    def recv(self, block: bool = True, timeout: float = None):
        # logger_utils_trace.debug("QueueItemRecv.recv(%s, %s)", block, timeout)
        item = self._queue.get(block=block, timeout=timeout)
        
        if self._is_end_fn(item):
            self.setEnded(True)
            raise Empty()

        return item
    
    def isEnded(self):
        return self.__isEnded
    
    def setEnded(self, ended:bool=True):
        """设置队列是否已结束

        Args:
            ended (bool, optional): 是否已结束. Defaults to True.
        """
        self.__isEnded = ended
