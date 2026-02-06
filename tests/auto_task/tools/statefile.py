import random

from smart.auto.run import auto_run
from smart.auto import AutoLoad

auto_load = AutoLoad()

@auto_load.func_task('test__shuffle')
def task_shuffle(task, item_iter=None, item_iter_fn=None):
    _item_iter = item_iter or (item_iter_fn or task.recv_data)()

    item_list = list(_item_iter)

    random.shuffle(item_list)

    print('### shuffled items:', item_list)

    for item in item_list:
        task.send_data(item)


def test_statefile():
    auto_run(
        'tests.auto_tasks.tools.test_tools',
        name='test_statefile',
        extra={} )


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)