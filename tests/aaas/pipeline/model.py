
import logging
import time, uuid

from smart.auto import TreeMultiTask, AutoLoad
from smart.utils.path import path_join


auto_load = AutoLoad()
task_hook = auto_load.hook

logger = logging.getLogger('tests')


@auto_load.task('tests__model_a')
class ModelA(TreeMultiTask):

    def prepare_data(self, dir_path, root_dir=None):
        '''
        recv: {"text": "abc"}
        send: {"text": "abc", ""}
        '''
        # Base config
        output_path = path_join(root_dir, dir_path)
    
    def train(self):
        '''
        Item Example-->
        recv: {"text": "abc"}
        send: {"text": "abc", "a_pred": uuid}
        '''
        for item in self.recv_data():
            item['a_pred'] = uuid.uuid1().hex
            self.send_data(item)
            # logger.debug('attach_guid: %s', item)

    def predict(self):
        '''
        Item Example-->
        recv: {"text": "abc"}
        send: {"text": "abc", "a_pred": uuid}
        '''
        for i, item in enumerate(self.recv_data()):
            item['a_pred'] = uuid.uuid1().hex
            self.send_data(item)
            time.sleep(.5)
            # self.context.state("predict_state").set("item_no", i)
            # if i > 4:
            #     raise Exception("Mock Predict Error")
            # logger.debug('attach_guid: %s', item)
    
    @task_hook.after_task('on_end')
    def on_end(self):
        logger.debug('ModelA on_end start')
        time.sleep(3)
        logger.debug('ModelA on_end done')


@auto_load.task('tests__model_b')
class ModelB(TreeMultiTask):

    def prepare_data(self, dir_path, root_dir=None):
        '''
        recv: {"text": "abc"}
        send: {"text": "abc", ""}
        '''
        # Base config
        output_path = path_join(root_dir, dir_path)
    
    def train(self):
        '''
        Item Example-->
        recv: {"text": "abc"}
        send: {"text": "abc", "b_pred": uuid}
        '''
        for item in self.recv_data():
            item['b_pred'] = uuid.uuid1().hex
            self.send_data(item)
            # logger.debug('attach_guid: %s', item)
    
    def predict(self):
        '''
        Item Example-->
        recv: {"text": "abc"}
        send: {"text": "abc", "b_pred": uuid}
        '''
        # 模拟加载模型到时间
        logger.info("load ModelB")
        for item in self.recv_data():
            item['b_pred'] = uuid.uuid1().hex
            self.send_data(item)
            # logger.debug('attach_guid: %s', item)
    
    @task_hook.after_task('on_end')
    def on_end(self):
        logger.debug('ModelB on_end start')
        time.sleep(3)
        logger.debug('ModelB on_end done')