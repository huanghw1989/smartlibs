from queue import Empty
import time

from smart.utils.common.timeout import min_timeout
from .BatchIter import BatchItemIter
from .ItemRecv import BaseItemRecv


class BatchItemRecv:
    def __init__(self, item_recv:BaseItemRecv) -> None:
        self._item_recv = item_recv

    def iter_fn(self, batch_size:int=2, block:bool=True, timeout:float=None, batch_timeout:float=None):
        """批处理获取数据; 每批第一条固定通过阻塞模式且不限超时时间地获取数据; 获取到第一条数据后, 开始计算整批次超时时间batch_timeout. 

        Args:
            batch_size (int, optional): 每批数据最大长度. Defaults to 2.
            block (bool, optional): 每批第2条起, 是否阻塞模式获取数据. Defaults to True.
            timeout (float, optional): 每批第2条起, 单次获取数据的超时时间. Defaults to None.
            batch_timeout (float, optional): 每批第2条起, 整批数据的超时时间. Defaults to None.

        Yields:
            list: item list
        """
        if block and timeout is None and batch_timeout is None:
            yield from BatchItemIter(self.recv_data(), batch_size).iter_fn()
            return
        
        if batch_timeout is not None and batch_timeout <= 0:
            # batch_timeout<=0等同于非阻塞模式获取数据
            block = False

        batch_item, ts_begin = [], None

        while not self._item_recv.isEnded():
            isBatchFirstItem = len(batch_item) == 0
            if isBatchFirstItem:
                # 每个batch的第1条数据都需要block方式接收队列数据
                _block, _timeout = True, None
                ts_begin = None
            else:
                _block = block
                rest_timeout = batch_timeout

                if block and batch_timeout is not None:
                    if ts_begin is None:
                        # 每个batch的第2条数据开始计算timeout
                        ts_begin = time.time()

                    # 计算批处理还剩余多少时间
                    rest_timeout = batch_timeout - time.time() + ts_begin
                    if rest_timeout <= 0:
                        # 剩余时间到了之后，改成通过非阻塞方式获取队列数据
                        _block = False

                if _block:
                    _timeout = min_timeout(timeout, rest_timeout)
                    _timeout = max(_timeout, 0)
                else:
                    # 非阻塞队列的timeout无意义
                    _timeout = None

            try:
                item = self._item_recv.recv(block=_block, timeout=_timeout)
                batch_item.append(item)
            except Empty:
                if len(batch_item):
                    yield batch_item
                    batch_item = []
                continue

            if len(batch_item) >= batch_size:
                yield batch_item
                batch_item = []
        
        # 补发队列结束后未达到batch_size的数据
        if len(batch_item):
            yield batch_item