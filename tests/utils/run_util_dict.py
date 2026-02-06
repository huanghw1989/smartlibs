"""Example:
python3 -m tests.utils.run_util_dict test_deep_merge
python3 -m tests.utils.run_util_dict test_safe_get
"""
import json

# from smart.utils import dict_deep_merge
from smart.utils.dict import *


def int_merge_sum(val_a, val_b, ctx_keys):
    if isinstance(val_a, int) and isinstance(val_b, int):
        return True, val_a + val_b


def test_deep_merge(no_copy=False):
    dict_a = {
        'config': {
            'a': {
                'b': 1,
                'c': 'x',
                'd': {
                    'e_a': 2,
                    'f': 'f_a',
                }
            }
        },
        "ab_key": {
            'x': 'a',
            'y_a': 2
        },
        "a_key1": 'hi',
        'a_key2': 222,
        "arr": [1, 2, 3],
    }
    dict_b = {
        'config': {
            'a': {
                'b': 'xxx',
                'f': 'yyy',
                'd': {
                    'e_b': 3,
                    'f': 'f_b',
                }
            }
        },
        "ab_key": {
            'x': 'b',
            'y_b': 2
        },
        "b_key": {
            'foo': 'bar'
        },
        "arr": [4, 5],
    }
    # dict_a_b = dict(dict_a, **dict_b)
    dict_a_b = {**dict_a, **dict_b}
    # from copy import deepcopy
    # dict_a_b = deepcopy(dict_a)
    # dict_a_b.update(dict_b)
    print('# merg_a_b', json.dumps(dict_a_b, indent=2))

    deep_merge_a_b = dict_deep_merge(dict_a, dict_b, no_copy=no_copy)
    print('# dict_deep_merge', json.dumps(deep_merge_a_b, indent=2))
    print('# dict_a', dict_a, dict_a==deep_merge_a_b)


def test_deep_merge_arr(merge_list=False, append_list=True, b_int_sum=False, no_copy=False):
    dict_a = {
        "arr": [1, 2, 3],
        'obj': {
            'int': 1,
            'arr': [1, 2, 3],
            'k_a': 'a',
            'any': 1
        }
    }
    dict_b = {
        "arr": [4, 5],
        'obj': {
            'int': 2,
            "arr": [4, 5],
            'k_b': 'b',
            'any': 'str',
        }
    }
    
    extra_fns = []
    if b_int_sum:
        extra_fns.append(int_merge_sum)

    merger = DictMerger(
        extra_fns=extra_fns, 
        no_copy=no_copy, 
        merge_list=merge_list, 
        append_list=append_list)

    deep_merge_a_b = merger.deep_merge(dict_a, dict_b)
    print('# dict_deep_merge', json.dumps(deep_merge_a_b, indent=2))


def test_safe_get():
    obj = {
        'a': {
            'b': 1
        }
    }
    all_key = [
        ['a', 'b'],
        None,
        'a',
        ['a', 'c', 'x'],
        'b'
    ]
    for key in all_key:
        print(key, ':', dict_safe_get(obj, key, 'No Value'))

def test_get_or_set():
    obj = [
        {}
    ]

    keys_val_list = [
        ((0, 'a'), None),
        ((0, 'a', 'b'), 1),
        ((0, 'a', 'c'), {}),
        ((0, 'a', 'c', 'd'), {}),
        ((0, 'a', 'c', 'd', 'e'), None),
    ]

    for keys, val in keys_val_list:
        print(keys, ':', dict_get_or_set(obj, keys, val))
    
    print('obj:', obj)


if __name__ == "__main__":
    import fire
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })