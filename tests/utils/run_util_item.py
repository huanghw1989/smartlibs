"""
python3 -m tests.utils.run_util_item test_group_by
"""
import time, pprint

from smart.utils.item import *

def test_group_by(n=10, only_group_val=False, copy_item=True, no_pop_group_key=False):
    item_iter = [
        {'id': i, 'cate': '12'[i % 2], 'val': 'abcdefghijk'[i % 10: i % 10+2], 'tag': 'xyz'[i % 3]}
        for i in range(n)
    ]
    print('items(origin):')
    pprint.pprint(item_iter)
    group_iter_fn = ItemGroupBy(item_iter, ['cate', 'tag']
        , only_group_val=only_group_val
        , copy_item=copy_item
        , no_pop_group_key=no_pop_group_key
        )
    group_item = list(group_iter_fn())
    print('\nGroup items:')
    pprint.pprint(group_item)
    if not copy_item:
        print('\nitems(after group):')
        pprint.pprint(item_iter)

if __name__ == "__main__":
    import fire
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })