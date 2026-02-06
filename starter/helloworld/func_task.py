from smart.auto.tree import *
from smart.auto import AutoLoad
auto_load = AutoLoad()

@auto_load.func_task('func_task__range', 'func_task.debug__range')
def task_range(task:TreeTask, end=1, start=0, step=1):
    for i in range(start, end, step):
        task.send_data(i)


@auto_load.func_task(config=['func_task.debug__print_head'])
def func_task__print_head(task:TreeTask, head:int=10, log_prefix='#{thread}-{idx}', timeout=10):
    idx = 0
    thread = task.options.get('worker_idx', 0)
    print('debug__print_head', head)
    for data in task.recv_data(block=True, timeout=timeout):
        if idx < head:
            if log_prefix:
                print(log_prefix.format(idx=idx, thread=thread), data)
            else:
                print(data)
        idx += 1