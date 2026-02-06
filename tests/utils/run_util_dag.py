from smart.utils.dag import *


def test_dag_tools():
    items = [
        {'id': 0, 'name': 'a', 'prev': [2, 3]},
        {'id': 1, 'name': 'b', 'prev': [0]},
        {'id': 2, 'name': 'c'},
        {'id': 3, 'name': 'd'},
    ]

    dag_tools = DagItemsTool(id_key_name='id', prev_key_name='prev')

    sort_items = [
        item
        for key, item in dag_tools.sort_items(items)
    ]

    print('ori items-->')
    for i, item in enumerate(items):
        print(i, item)

    print('\nsort items-->')
    for i, item in enumerate(sort_items):
        print(i, item)



def test_find_cycle():
    dependance_set = set([
        ('a', 'b'),
        ('b', 'c'),
        ('b', 'd'),
        ('d', 'a'),
    ])

    # dag_assert_no_cycle(dependance_set)
    cycle = dag_find_cycle(dependance_set)
    print('dependance_set-->')
    for key_a, key_b in dependance_set:
        print('{} -> {}'.format(key_a, key_b))
        
    print('cycle: ', cycle)


if __name__ == "__main__":
    import fire
    
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })