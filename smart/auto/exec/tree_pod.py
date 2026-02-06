import time, sys, typing

from smart.auto.exec.tree_exec import TreeTaskExecutor
from smart.auto.exec.worker import BaseWorker
from smart.auto.exec.task_pod import TaskPod
from smart.auto.tree import TreeContext
from smart.auto.meta import TreeMeta, TreeTaskMeta

from smart.auto.__logger import logger
from smart.utils.env import AppEnv


class TreePod:
    def __init__(self, tree_name:str, tree:TreeMeta, context:TreeContext) -> None:
        self.tree_name = tree_name
        self.tree = tree
        self.context = context
        self.task_pod_list:typing.List[TaskPod] = []
        self.__started = False

    def start(self):
        if self.__started:
            logger.warning("TreePod.start should call once")
            return
        self.__started = True

        tree_name, tree, context = self.tree_name, self.tree, self.context

        # Execute before_task hook
        for tree_task_meta in tree.tree_tasks:
            tree_task_meta:TreeTaskMeta
            task_meta = tree_task_meta.task_meta
            task_executor:TreeTaskExecutor = task_meta.task_executor
            task_executor.run_hook('before_task', context=context)
        
        if context.is_stop_task(end_all=True):
            logger.info('# Tree %s is stop by flag context.stop_task', tree_name)
            return

        for tree_task_meta in tree.tree_tasks:
            tree_task_meta:TreeTaskMeta
            
            exec_opts = tree_task_meta.exec_opts
            task_meta = tree_task_meta.task_meta
            task_executor:TreeTaskExecutor = task_meta.task_executor

            task_pod = task_executor.exec_fn(**exec_opts)
            self.task_pod_list.append(task_pod)
    
    def join(self):
        # 启用远程调试功能
        if AppEnv.get('DEBUG_KILL_TASK'):
            from smart.utils.remote_debug import enable_remote_debug
            enable_remote_debug()

        tree_name, tree, context = self.tree_name, self.tree, self.context
        
        to_kill_pods:typing.List[TaskPod] = []
        kill_reason, exec_opts = None, None

        try:
            for task_pod in self.task_pod_list:
                task_pod.join()
                if len(task_pod._to_kill_workers):
                    to_kill_pods.append(task_pod)

            # Execute after_task hook
            for tree_task_meta in tree.tree_tasks:
                tree_task_meta:TreeTaskMeta
                task_meta = tree_task_meta.task_meta
                task_executor:TreeTaskExecutor = task_meta.task_executor
                task_executor.run_hook('after_task', context=context)

            if len(to_kill_pods):
                logger.debug("to_kill_workers: %s", [
                    (tp.task_meta.task_key, tp._to_kill_workers)
                    for tp in to_kill_pods
                ])
                time.sleep(1)
        except KeyboardInterrupt:
            to_kill_pods = self.task_pod_list
            for task_pod in to_kill_pods:
                task_pod._to_kill_workers = task_pod.worker_list
            kill_reason = 'keyword interrupt'
        finally:
            # Make sure process exit
            for i in range(2):
                all_done = True
                if i > 0:
                    time.sleep(1)
                for task_pod in to_kill_pods:
                    task_meta = task_pod.task_meta
                    for worker in task_pod._to_kill_workers:
                        if worker.is_alive():
                            logger.debug('kill worker %s because %s', task_meta.task_key, kill_reason or 'task is done')
                            worker.forceStop()
                            all_done = False
                if all_done:
                    break
            logger.debug('Tree %s is done %s', tree_name, exec_opts)