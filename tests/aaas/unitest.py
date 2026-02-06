
from smart.auto import TreeMultiTask, AutoLoad
from . import logger

auto_load = AutoLoad()
task_hook = auto_load.hook


@auto_load.task('test.aaas__unitest')
class TestAaasUnitestTask(TreeMultiTask):
    def mock_err(self):
        for item in self.recv_data():
            raise Exception("aaas__unitest mock_err")