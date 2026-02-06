# python -m tests.evals.core.item item_list
# python -m tests.evals.core.item item_matrix
from smart.evals.core.filter_op import *
from smart.evals.core.item import *
from tests.evals import logger
import random, pprint



def test_item_list():
    items = ItemList([
        {'x': 1},
        {'x': 2},
        {'x': 3},
    ])
    num = len(items)
    logger.info('len(item): %s', num)
    for item in items:
        logger.info('item: %s', item)

    logger.info('items[0]: %s', items[0])
    logger.info('items[:2]: %s', items[:2])


def test_item_matrix(num_row:int=10, append_no_match_item:bool=True):
    item_matrix = ItemMatrix.from_list(
        item_list=[
            {'id':id, 'value': random.randint(0, num_row)}
            for id in range(num_row)
        ]
    )
    new_items = ItemList(
        data=[
            {'id':id+2, 'value': random.randint(-num_row, 0)}
            for id in range(num_row)
        ]
    )
    item_matrix.join_items(
        item_list=new_items,
        column_name='new',
        id_key='id',
        append_no_match_item=append_no_match_item
    )
    logger.info('item_matrix:\n%s', pprint.pformat(item_matrix.to_list()))

    op = FilterOp()
    filterd_matrix = item_matrix.filter(
        op.any([
            op.val_in_range((1, 'value'), start=-6, end=-1)
        ])
    )
    logger.info('filterd_matrix:\n%s', pprint.pformat(filterd_matrix.to_list()))

    col2_items = item_matrix.column_data('new')
    logger.info('col2_items:\n%s', pprint.pformat(col2_items.to_list()))


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)