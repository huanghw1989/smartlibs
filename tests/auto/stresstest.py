import time, random, string
from smart.auto.tree import TreeMultiTask

from .__init__ import auto_load, logger


@auto_load.task('stresstest')
class StressTest(TreeMultiTask):
    def mock_data(self, size:int=10, batch:int=100, text_len:int=10):
        logger.info('### mock_data size=%d, batch=%d, text_len=%d', size, batch, text_len)

        if text_len >= 20:
            _text_prefix = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(text_len-10))
            text_len = 10
        else:
            _text_prefix = ''

        def _item_iter_fn():
            for i in range(size):
                item = []
                for j in range(batch):
                    item.append({
                        'i': i,
                        'j': j,
                        'ts': time.time(),
                        'text': _text_prefix + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(text_len))
                    })
                yield item

        return {
            'item_iter_fn': _item_iter_fn
        }