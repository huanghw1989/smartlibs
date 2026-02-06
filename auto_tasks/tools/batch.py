from queue import Empty
import time

from smart.auto.tree import TreeMultiTask
from smart.auto.pip.QueuePipItemRecv import QueuePip, QueuePipItemRecv
from smart.utils.batch.BatchItemRecv import BatchItemRecv
from .__utils import auto_load, logger


@auto_load.task('tools.batch')
class BatchTask(TreeMultiTask):
    def recv(self, batch_size:int=2, block:bool=True, timeout:float=None, batch_timeout:float=None):
        _pip_in = self.pip_in
        if not isinstance(_pip_in, QueuePip):
            raise Exception("BatchTask.recv only support QueuePip")
        
        item_recv = QueuePipItemRecv(pip=_pip_in)

        batch_recv = BatchItemRecv(item_recv=item_recv)
        batch_iter = batch_recv.iter_fn(
            batch_size=batch_size,
            block=block,
            timeout=timeout,
            batch_timeout=batch_timeout
        )

        return {
            "item_iter": batch_iter
        }