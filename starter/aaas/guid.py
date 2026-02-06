import uuid, logging
import time

from smart.auto import TreeMultiTask, AutoLoad


auto_load = AutoLoad()
task_hook = auto_load.hook

logger = logging.getLogger('guid')


@auto_load.task('example__guid')
class GuidTask(TreeMultiTask):
    
    def attach_guid(self, id_key='guid'):
        for item in self.recv_data():
            item[id_key] = uuid.uuid1().hex
            self.send_data(item)
            logger.debug('attach_guid: %s', item)
    
    @task_hook.after_task('on_end')
    def on_end(self):
        logger.debug('GuidTask on_end start')
        time.sleep(3)
        logger.debug('GuidTask on_end done')