import time
from smart.auto import TreeMultiTask, AutoLoad

auto_load = AutoLoad()

@auto_load.task("tests.batch_mock_handle")
class MockHandleTask(TreeMultiTask):
    def handle(self, item_iter=None, item_iter_fn=None):
        _item_iter = item_iter or item_iter_fn()

        for i, item in enumerate(_item_iter):
            if i%2 == 0:
                time.sleep(0.2)
            self.send_data(item)