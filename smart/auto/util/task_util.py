from smart.auto.tree import TreeTask
from smart.auto.__logger import logger


class TreeTaskUtil:
    def __init__(self, task:TreeTask) -> None:
        self._task = task
    
    def worker_ctx_state(self):
        task = self._task
        worker_idx = task.worker_state.worker_idx
        state = task.context.state((task.task_key, worker_idx))
        return state

    def safe_recv_data(self):
        task_run_count = self._task.worker_state.get('task_run_count') or 0
        state = self.worker_ctx_state()
        last_item_tuple = state.get('last_item')
        if last_item_tuple is not None:
            prev_run_count, last_item = last_item_tuple
            if prev_run_count < task_run_count:
                # 重新运行任务时, 需返回上一次运行任务的最后一条数据
                logger.debug("TreeTaskUtil.safe_recv_data task_run_count=%s last_item: %s", task_run_count, last_item_tuple)
                yield last_item
        for item in self._task.recv_data():
            state.set('last_item', (task_run_count, item))
            yield item
        state.delete('last_item')