import time
from smart.auto import TreeMultiTask
from tests.auto import logger, auto_load

@auto_load.task("tests.test_pip_queue")
class TestQueuePipTask(TreeMultiTask):
    def multi_recv(self, timeout=10):
        logger.info("TestQueuePipTask.multi_recv begin")
        for i, item in enumerate(self.recv_data()):
            logger.info("TestQueuePipTask.multi_recv Recv1-%s: %s", i, item)

        time_begin = time.time()
        for i, item in enumerate(self.recv_data(timeout=timeout)):
            logger.info("TestQueuePipTask.multi_recv Recv2-%s: %s", i, item)
        if time.time() - time_begin > max(timeout-1, 1):
            raise Exception("recv_data again took too much time, expect less than {} seconds".format(max(timeout-1, 1)))
        
        # self.pip_in.queue.get(timeout=5)

        logger.info("TestQueuePipTask.multi_recv end")