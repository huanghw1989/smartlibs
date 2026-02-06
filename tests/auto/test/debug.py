import time
from smart.auto.tree import TreeTask
from tests.auto import logger


def task_range(task:TreeTask, end=1, start=0, step=1):
    logger.info("task_range end=%s, start=%s, step=%s", end, start, step)
    for i in range(start, end, step):
        task.send_data(i)


def task_print_head(task:TreeTask, head=10, log_prefix='#{thread}-{idx}', timeout=10):
    idx = 0
    thread = task.options.get('worker_idx', 0)
    for data in task.recv_data(block=True, timeout=timeout):
        if idx < head:
            if log_prefix:
                print(log_prefix.format(idx=idx, thread=thread), data)
            else:
                print(data)
        idx += 1
        time.sleep(0.05)