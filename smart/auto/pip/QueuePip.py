from queue import Queue, Empty
import multiprocessing as mp

from smart.auto.base import BasePip
from smart.auto.pip.cmd import Command, CommandType

from ..__logger import logger


class QueuePip(BasePip):
    """队列管道
    """
    def __init__(self, queue:Queue=None, on_end:callable=None):
        self.queue = queue or Queue()
        self.on_end = on_end
        self.is_ended = False

    def send(self, data, block=True, timeout=None, **kwargs):
        self.queue.put(data, block=block, timeout=timeout)

    def recv(self, block=True, timeout=None, raise_empty=False, on_cmd:callable=None, 
                block_fn:callable=None, timeout_fn:callable=None, 
                end_on_timeout:bool=True, on_timeout:callable=None, **kwargs):
        """接收数据
        
        Keyword Arguments:
            block {bool} -- 当队列中无数据时, 是否阻塞队列 (default: {True})
            timeout {float} -- 当队列中无数据时, 经过timeout秒后结束 (default: {None})
            raise_empty {bool} -- 获取超时时, 是否抛出Empty异常 (default: {False})
            on_cmd {callable} -- 当收到CommandType.app的数据, 触发 on_cmd
            block_fn {callable} -- 获取block值的函数; 当block_fn不为空时, block参数失效. Defaults to None.
            timeout_fn {callable} --  获取timeout值的函数; 当timeout_fn不为空时, timeout参数失效. Defaults to None.
            end_on_timeout {bool} -- 当队列获取超时, 是否结束生成器; False时, 将yield None; 当raise_empty=True时, end_on_timeout参数无效. Defaults to True.
            on_timeout {callable} --  当队列获取超时, 调用on_timeout函数. Defaults to None.
        
        Raises:
            Empty: 队列无数据
        
        Yields:
            any -- 接收到的数据
        """
        try:
            _queue = self.queue
            if not _queue:
                yield from []
                return

            while not self.is_ended:
                _block = block if block_fn is None else block_fn()
                _timeout = timeout if timeout_fn is None else timeout_fn()

                try:
                    # logger.debug('QueuePip.recv get %s, %s', _block, _timeout)
                    data = _queue.get(block=_block, timeout=_timeout)
                except Empty as e:
                    timeout_item = None
                    if on_timeout:
                        timeout_item = on_timeout()

                    if raise_empty:
                        raise e
                    elif end_on_timeout:
                        break
                    else:
                        yield timeout_item
                        continue
                
                if isinstance(data, Command):

                    if data.type == CommandType.end:

                        self.is_ended = True
                        if self.on_end:
                            self.on_end(data)

                        break
                    elif data.type == CommandType.app:

                        if on_cmd:
                            on_cmd(**data.args)
                else:
                    yield data
            # logger.debug('QueuePip.recv end')
        except KeyboardInterrupt:
            
            logger.info('QueuePip.recv end(KeyboardInterrupt)')
            # 关闭 queue, 避免循环recv
            self._old_queue = self.queue
            self.queue = None 
    
    def clean(self, no_data=True, **kwargs):
        _queue = self.queue or self._old_queue

        if not _queue:
            return None
        
        clean_counter = 0

        def _item_iter_fn():
            nonlocal clean_counter

            try:

                while True:
                    item = _queue.get(block=True, timeout=.1)
                    yield item
                    clean_counter += 1
            except Empty:
                pass
        
        _item_iter = _item_iter_fn()
        
        if no_data:
            for _ in _item_iter:
                pass

            return clean_counter
        else:
            return _item_iter