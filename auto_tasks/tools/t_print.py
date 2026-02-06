import os

from smart.auto.tree import TreeMultiTask

from smart.utils.yaml import yaml_dumps
from smart.utils.list import list_safe_iter
from smart.utils import AppEnv

from .__utils import auto_load, logger


@auto_load.task('tools.print', alias=['tools__print'])
class PrintTask(TreeMultiTask):

    @staticmethod
    def _print(item_iter, head:int, format=None):
        for i, item in enumerate(item_iter):
            if head not in (None, '') and i >= head: break

            PrintTask._log_item(item, i, format=format)
    
    @staticmethod
    def _log_item(item, idx, format=None):
        if format in ('yml', 'yaml'):
            item = yaml_dumps({'yml': item})

        logger.info('PrintTask item %d - %s', idx, item)

    def item_iter(self, head:int=10, format=None, item_iter=None, item_iter_fn=None):
        logger.debug('tools__print.item_iter head=%s', head)
        item_iter = item_iter or (item_iter_fn or self.recv_data)()
        PrintTask._print(item_iter, head, format=format)
    
    def head(self, head:int=10, item_iter=None, item_iter_fn=None):
        item_iter = item_iter or (item_iter_fn or self.recv_data)()

        logger.debug('PrintTask.head %s', head)

        def item_iter_fn():
            for i, item in enumerate(item_iter):
                if head not in (None, '') and i >= head: break
                yield item
        
        return {
            'item_iter': item_iter_fn(),
            'item_iter_fn': item_iter_fn
        }
    
    def watch(self, head:int=10, step=1000, format=None, item_iter=None, item_iter_fn=None):
        _item_iter = item_iter or (item_iter_fn or self.recv_data)()

        logger.debug('PrintTask.watch %s head=%s, step=%s', self.task_key, head, step)

        def _item_iter_fn():
            count = 0
            for i, item in enumerate(_item_iter):
                if head in (None, '') or (i < head):
                    PrintTask._log_item(item, i, format=format)
                
                if (i + 1) % step == 0:
                    logger.info('PrintTask %s step %s', self.task_key, i+1)
                
                yield item
                count += 1
            
            logger.info('PrintTask total item: %s', count)
        
        if item_iter or item_iter_fn:
            return {
                'item_iter': _item_iter_fn(),
                'item_iter_fn': _item_iter_fn
            }
        else:
            for item in _item_iter_fn():
                self.send_data(item)

    def step(self, step=1000, only_idx=False, item_iter=None, item_iter_fn=None):
        item_iter = item_iter or (item_iter_fn or self.recv_data)()

        logger.debug('PrintTask.log step=%s', step)
        
        def item_iter_fn():
            for i, item in enumerate(item_iter):
                if (i + 1) % step == 0:
                    if only_idx:
                        logger.info('PrintTask.step %s', i+1)
                    else:
                        logger.info('PrintTask.step %s: %s', i+1, item)
                yield item

        return {
            'item_iter': item_iter_fn(),
            'item_iter_fn': item_iter_fn
        }
    
    def all_params(self, **kwargs):
        logger.info('tools_print.all_params')

        for arg_name, arg_val in kwargs.items():
            arg_type_name = getattr(type(arg_val), '__name__', type(arg_val))
            logger.info('\t%s:%s=%s', arg_name, arg_type_name, arg_val)
        
        return kwargs
    
    def env(self, env_names:list=None):
        for env_name in list_safe_iter(env_names):
            if env_name:
                env_val = os.environ.get(str(env_name))
                env_type = "os"
                
                if env_val is None:
                    env_val = AppEnv.get(str(env_name), include_sys=False)
                    if env_val is not None:
                        env_type = "app"

                logger.info("PrintTask.env %s.environ %s=%s", env_type, env_name, env_val)