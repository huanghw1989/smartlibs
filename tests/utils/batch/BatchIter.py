from tests.utils import logger
from smart.utils.batch.BatchIter import *


def test_batch(batch=3, n=10):
    item_iter = range(n)
    batch_item_iter = BatchItemIter(item_iter, batch).iter_fn()

    for i, item in enumerate(batch_item_iter):
        logger.info("test_batch %d, %s", i, item)


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)