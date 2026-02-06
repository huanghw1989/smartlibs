from typing import List

from smart.utils.func import func_safe_call
from smart.utils.bound import Bound

from smart.auto.base import BaseTask
from smart.auto.pip import Broadcast, Command, CommandType

from smart.auto.ctx.tree_context import TreeContext
from smart.auto.ctx.worker_state import WorkerState

from smart.auto.__logger import logger


class TreeTask(BaseTask):
    """一对多的任务流基类
    设计思路: 每个 TreeTask 可以有多个下游任务, 但只有一个上游任务; 上游任务通过 Broadcast 向下游任务发送数据
    """
    def __init__(self, pip_out_fn:callable=None, context:TreeContext=None, task_key=None, **options):
        """构造函数
        
        Keyword Arguments:
            pip_out_fn {callable} -- 缺省值None将自动替换为lambda:QueuePip() (default: {None})
        """
        pip_out = Broadcast(pip_fn=pip_out_fn)
        self._main_task = None
        self._join_task_list:List[BaseTask] = []
        super().__init__(pip_out=pip_out, pip_in=None, context=None)
        self._context = context
        self.prev_task = None
        self.next_tasks = []
        self.options = options
        self.task_key = task_key
        self.worker_state = WorkerState()
    
    @BaseTask.pip_in.setter
    def pip_in(self, val):
        self._pip_in = val
        for task in self._join_task_list:
            task.pip_in = val
    
    @BaseTask.pip_out.setter
    def pip_out(self, val):
        self._pip_out = val
        for task in self._join_task_list:
            task.pip_out = val
    
    @property
    def context(self) -> TreeContext:
        return self._context

    @context.setter
    def context(self, val):
        self._context = val
        for task in self._join_task_list:
            task.context = val

    def send_cmd(self, type:CommandType=CommandType.app, **kwargs):
        """发送命令
        
        Keyword Arguments:
            type {CommandType} -- 命令类型 (default: {CommandType.app})
        """
        self.send_data(Command(
            type=type,
            **kwargs
        ))
    
    def join_task(self, task:BaseTask):
        self._join_task_list.append(task)
        task.pip_in = self.pip_in
        task.pip_out = self.pip_out
        task.context = self.context
        task.worker_state = self.worker_state
        task._main_task = self

    def next(self, task:BaseTask)->BaseTask:
        """设置下游任务
        
        Arguments:
            task {TreeTask} -- Tree任务
        
        Returns:
            TreeTask -- self
        """
        self.next_tasks.append(task)

        new_pip = self.pip_out.create_pip()

        task.prev_task = self
        task.pip_in = new_pip

        return self

    def nexts(self, tasks:List[BaseTask])->BaseTask:
        """设置多个下游任务
        
        Arguments:
            tasks {List[TreeTask]} -- 任务列表
        
        Returns:
            TreeTask -- self
        """
        for task in tasks:
            self.next(task)

        return self
    
    def stop_task(self, end_all=False):
        """停止任务 (仅能在 before_task 勾子函数中调用)

        Keyword Arguments:
            end_all {bool} -- True 表示停止整个任务树, False 表示仅停止当前任务单元 (default: {False})
        """
        if self.context:
            self.context.stop_task(
                self.task_key,
                end_all=end_all
            )
        else:
            logger.warning('stop_task fail because context is None')
    
    def is_stop_task(self, end_all=True):
        """任务是否被停止

        Keyword Arguments:
            end_all {bool} -- True表示同时判断任务和任务树的停止标记 (default: {True})

        Returns:
            bool -- b_stop_task
        """
        return self.context.is_stop_task(
            task_key=self.task_key,
            end_all=end_all
        ) if self.context else False


class TreeFuncTask(TreeTask):
    """函数转TreeTask
    Case - 向管道发送自然数序列
    def send_func(task:TreeTask, n):
        for i in range(n):
            task.send_data(i)
    send_task = TreeFuncTask(send_func)
    send_task.start(5)
    """
    def __init__(self, run_func:callable, **kwargs):
        self.run_func = run_func
        super().__init__(**kwargs)

    def start(self, *args, **kwargs):
        return func_safe_call(self.run_func, [self, *args], kwargs)


class TreeLambdaTask(TreeTask):
    """lambda函数转TreeTask
    Case - 将管道数据重复1倍
    TreeLambdaTask(lambda data: [data] * 2)
    """
    def __init__(self, lambda_func:callable, **kwargs):
        self.run_func = lambda_func
        super().__init__(**kwargs)
        
    def start(self, block=False, timeout=None, *args, **kwargs):
        for data in self.recv_data(block=block, timeout=timeout):
            for to_send in self.run_func(data, *args, **kwargs) or []:
                self.send_data(to_send)


class TreeMultiTask(TreeTask):
    """多任务类, 可以自定义多个执行函数; 启动任务时(即执行start函数), 第一参数传入执行函数名
    """
    def start(self, func_name:str, *args, **kwargs):
        """启动入口
        
        Arguments:
            func_name {str} -- 执行函数名
        """
        func = getattr(self, func_name)
        func(*args, **kwargs)


class TreeModuleTask(TreeMultiTask):
    """module as TreeTask
    """
    def __init__(self, module, *args, **kwargs):
        # self.module = module
        self.__dict__ = {
            'module': module
        }
        super().__init__(**kwargs)
        
    def __getattr__(self, name):
        # print('__getattr__', name)
        if name[:2] == '__':
            return object.__getattribute__(self, name)
            
        if name not in self.__dict__:
            self.__dict__[name] = Bound(self, getattr(self.__dict__['module'], name))

        return self.__dict__.get(name)

# deprecated
# TreeMutilTask = TreeMultiTask
