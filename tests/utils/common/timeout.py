# python3 -m tests.utils.common.timeout min_timeout '[None, 1.1]', '[-1, -2]'
from smart.utils.common.timeout import *
from tests.utils import logger


def test_min_timeout(*vals_list):
    if not vals_list:
        vals_list = [
            [None],
            [None, None],
            [None, None, None],
            [1.1, 2.1, None],
            [-0.1, None],
            [None, 0.1],
            [-0.2, -0.3, 1.1, 1.2]
        ]
    
    for vals in vals_list:
        min_val = min_timeout(*vals)
        logger.info("test_min_timeout %s => %s", vals, min_val)
    


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)