"""Example:
python3 -m tests.auto.run_tree test_tree_task
python3 -m tests.auto.run_tree test_tree_task info
python3 -m tests.auto.run_tree test_tree_module
"""
import fire

from smart.utils import dyn_import

from smart.auto.tree import *
from smart.auto.exec.tree_exec import *
from smart.auto.pip import end_cmd


class LogTask(TreeMultiTask):
    def info(self):
        for data in self.recv_data(block=False):
            print('[info]', data)
    def debug(self):
        for data in self.recv_data(block=False):
            print('[debug]', data)


def send_func(task:TreeTask, n):
    for i in range(n):
        task.send_data(i)
        print('task1 send', i)


def recv_func_fn(func_name):
    def recv_func(task:TreeTask):
        for data in task.recv_data(block=False):
            print(func_name, 'recv', data)
    return recv_func


def forward_func_fn(func_name):
    def forward_func(task:TreeTask):
        for data in task.recv_data(block=False):
            print(func_name, 'recv', data)
            task.send_data((data, func_name))
    return forward_func


def test_tree_task(log='debug'):
    # init task
    send_task = TreeFuncTask(send_func)
    forward_task1 = TreeFuncTask(forward_func_fn('forward_task1'))
    forward_task2 = TreeLambdaTask(lambda data: [(data, 'forward_task2')] * 2)
    recv_task1 = TreeFuncTask(recv_func_fn('recv_task1'))
    recv_task2 = TreeFuncTask(recv_func_fn('recv_task2'))
    log_task = LogTask()
    # define tree
    send_task.nexts([
        forward_task1.next(
            recv_task1
        ),
        forward_task2.nexts([
            recv_task2,
            log_task
        ])
    ])
    # run all task
    send_task.start(3)
    for task in (forward_task1, forward_task2, recv_task1, recv_task2):
        task.start()
    log_task.start(log)


def test_tree_module():
    m = dyn_import('tests.auto.test.debug')
    t1 = TreeModuleTask(m)
    t2 = TreeModuleTask(m)
    t1.next(t2)
    t1.task_range(10)
    t1.send_data(end_cmd)
    t2.task_print_head()


if __name__ == "__main__":
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })