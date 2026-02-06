from smart.auto.tree import TreeMultiTask
from .__utils import auto_load, logger


@auto_load.task('tools.pager', alias='tools__pager')
class PagerTask(TreeMultiTask):
    def page(self, page_num=1, page_size=10, item_iter=None, item_iter_fn=None, recv_rest=True):
        item_iter = item_iter or (item_iter_fn or self.recv_data)()
        logger.info('tools_pager.page %s', (page_num, page_size))

        def item_iter_fn():
            start, end = (page_num-1) * page_size, page_num*page_size

            for i, item in enumerate(item_iter):
                if i < start: 
                    continue

                if i >= end:
                    if recv_rest:
                        for _ in item_iter:
                            pass
                    break
                
                yield item

        return {
            'item_iter_fn': item_iter_fn,
            'pagination': (page_num, page_size)
        }