from .__init__ import TreeMultiTask, logger, auto_load
import time

@auto_load.task("fault_handle")
class FaultHandleTest(TreeMultiTask):
    def task1(self, n=10):
        for i in range(n):
            self.send_data({"i": i, "ts": time.time()})

        logger.info("## task1 end")
        raise Exception("task1 mock exception")

    def task2(self):
        _item_iter = self.recv_data()

        for i, item in enumerate(_item_iter):
            logger.info("task2 %s, %s", i, item)
            time.sleep(0.01)
        
        logger.info("## task2 end")

