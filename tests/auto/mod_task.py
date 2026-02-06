from .__init__ import auto_load, TreeTask, logger

# 自动装载 module_task
auto_load.module_task(__name__, name='mod_task')

# @auto_load.pod('lambda')
def repeat_item(item, repeat=2):
    for i in range(repeat):
        yield item

def mock_data(task:TreeTask, start:int=0, end:int=5, step:int=1):
    logger.debug("%s mock_data enter", task)
    def _item_iter_fn():
        for i in range(start, end, step):
            yield 'module_task.range {}'.format(i)
    
    return {
        'item_iter': _item_iter_fn()
    }


def print_data(task:TreeTask, head:int=5, item_iter=None, item_iter_fn=None):
    _item_iter = item_iter or item_iter_fn()
    i = -1

    for i, item in enumerate(_item_iter):
        if head is None or i < head:
            logger.info('module_task.print_data %s %s', i, item)
    
    logger.info('module_task.print_data recv %s items', i+1)