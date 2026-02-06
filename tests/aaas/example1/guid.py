import uuid, logging
import time, random

from smart.auto import TreeMultiTask, AutoLoad


auto_load = AutoLoad()
task_hook = auto_load.hook

logger = logging.getLogger('guid')


@auto_load.task('test.example__guid')
class GuidTask(TreeMultiTask):
    def extract(self, size:int=10):
        for i in range(size):
            item = {
                "i": i,
                "_ts_req": time.time()
            }
            self.send_data(item)
    
    def transform(self):
        for item in self.recv_data():
            item["value"] = random.random()
            self.send_data(item)
    
    def attach_guid(self, id_key='guid'):
        for item in self.recv_data():
            item[id_key] = uuid.uuid1().hex
            item["_ts_resp"] = time.time()
            self.send_data(item)
            logger.debug('attach_guid: %s', item)
    
    @task_hook.after_task('on_end')
    def on_end(self):
        logger.debug('GuidTask on_end start')
        time.sleep(3)
        logger.debug('GuidTask on_end done')