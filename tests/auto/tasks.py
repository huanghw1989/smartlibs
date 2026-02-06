import datetime, random

from smart.utils.yaml import yaml_dumps
from smart.utils.common.value import if_null
from smart.auto.util.task_util import TreeTaskUtil
from .__init__ import logger, auto_load, TreeMultiTask


@auto_load.task("test_tasks")
class TestTasks(TreeMultiTask):
    def __init__(self, pip_out_fn: callable = None, context = None, task_key=None, **options):
        logger.debug("TestTasks.__init__ %s", options)
        super().__init__(pip_out_fn, context, task_key, **options)
        self.util = TreeTaskUtil(self)
    
    def attach_mayerr(self, err_prob:float=0.3, must_err:bool=False):
        worker_idx = self.worker_state.worker_idx
        logger.info('### TestTasks.attach_mayerr$%s task_key=%s, err_prob=%s, worker_state=%s', 
                if_null(worker_idx, '_'), self.task_key, err_prob, self.worker_state.to_dict())

        for item in self.util.safe_recv_data():
            d = datetime.datetime.today()
            item['time'] = d.strftime("%Y-%m-%d %H:%M:%S.%f")
            self.send_data(item)
            if random.random() < err_prob:
                raise Exception("TestTasks.attach_mayerr triger mock error")
        
        if must_err:
            raise Exception("TestTasks.attach_mayerr triger mock error2")

    @staticmethod
    def _log_item(item, idx, format=None):
        if format in ('yml', 'yaml'):
            item = yaml_dumps({'yml': item})

        logger.info('TestTasks item %d - %s', idx, item)

    def watch(self, head:int=10, step=1000, format=None, item_iter=None, item_iter_fn=None):
        _item_iter = item_iter or (item_iter_fn or self.recv_data)()

        logger.debug('%s watch %s head=%s, step=%s, task_options=%s', 
                self, self.task_key, head, step, self.options)
        self._test_watch = {
            'head': head,
            'step': step,
            'format': format
        }

        def _item_iter_fn():
            count = 0
            for i, item in enumerate(_item_iter):
                if head in (None, '') or (i < head):
                    TestTasks._log_item(item, i, format=format)
                
                if (i + 1) % step == 0:
                    logger.info('TestTasks %s step %s', self.task_key, i+1)
                
                yield item
                count += 1
            
            logger.info('TestTasks total item: %s', count)
        
        if item_iter or item_iter_fn:
            return {
                'item_iter': _item_iter_fn(),
                'item_iter_fn': _item_iter_fn
            }
        else:
            for item in _item_iter_fn():
                self.send_data(item)
    
    def print_params(self, **kwargs):
        logger.info("%s.print_params kwargs=%s, self.options=%s, self._test_watch=%s", 
            self, kwargs, self.options, getattr(self, '_test_watch', None))