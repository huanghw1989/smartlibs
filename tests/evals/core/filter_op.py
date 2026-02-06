# python -m tests.evals.core.filter_op op
from smart.evals.core.filter_op import *
from tests.evals import logger


def test_op():
    op = FilterOp()
    op1 = op.all([
        op.startswith('x', ['a']),
        op.endswith('x', ['a'])
    ])
    op1_not = op._not(op1)
    item_list = [
        {'x': 'a_a'},
        {'x': 'a_1'},
        {'x': 'b_b'},
    ]
    for item in item_list:
        logger.info('op1: %s -> %s', item, op1(item))
        logger.info('op1_not: %s -> %s', item, op1_not(item))


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)