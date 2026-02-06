from enum import Enum
import re


class FuncMeta:
    def __init__(self, **kwargs):
        self.func_name:str = kwargs.get('func_name')
        self.func_args:list = kwargs.get('func_args')
        self.func_kwargs:dict = kwargs.get('func_kwargs')
        self.func_obj:callable = kwargs.get('func_obj')


class TaskMeta:
    def __init__(self, **kwargs):
        self.task_class = kwargs.get('task_class')
        self.task_class_path = kwargs.get('task_class_path') # dotted_class_path
        self.task_dict:dict = kwargs.get('task_dict') # run_obj任务节点
        self.task_name = kwargs.get('task_name')
        self.task_key_info:TaskKeyInfo = kwargs.get('task_key_info')
        self.func_name = kwargs.get('func_name')
        self.task_method_meta:TaskMethodMeta = kwargs.get('task_method_meta')
        self.task_obj = kwargs.get('task_obj')
        self.task_type:EnumTaskType = kwargs.get('task_type') or EnumTaskType.default_val
        self.ext_task_meta:TaskMeta = kwargs.get('ext_task_meta')
        self.task_executor = kwargs.get('task_executor')

    @property
    def task_key(self):
        return self.task_key_info.full_key if self.task_key_info else None


class TaskKeyInfo:
    def __init__(self, **kwargs):
        self.full_key = kwargs.get('full_key')
        self.cls_key = kwargs.get('cls_key')
        self.func_key_type = kwargs.get('func_key_type')

        func_key = kwargs.get('func_key')
        if func_key:
            self.func_key = func_key
        else:
            self.func_name = kwargs.get('func_name')
            # 任务树通过 func_name_tail 实现同一任务函数用于多个任务节点
            self.func_name_tail = kwargs.get('func_name_tail')
    
    @staticmethod
    def parse_func_name_tail(func_key):
        if not func_key:
            return func_key, None

        matched = re.search(r'\$\d+$', func_key)
        
        if matched:
            pos = matched.start()
            return func_key[:pos], func_key[pos:]
        else:
            return func_key, None
    
    @property
    def func_key(self):
        return (self.func_name or '') + (self.func_name_tail or '')
    
    @func_key.setter
    def func_key(self, func_key):
        func_name, func_name_tail = self.parse_func_name_tail(func_key)
        self.func_name = func_name
        self.func_name_tail = func_name_tail

    @property
    def func_is_ext(self):
        return self.func_key_type == '@'


class EnumTaskType(Enum):
    default_val = None
    ext = 'ext'
    func_task = 'func_task'


class TreeTaskMeta:
    def __init__(self, task_meta:TaskMeta = None, **kwargs):
        self.task_meta = task_meta
        self.exec_opts = kwargs.get('exec_opts')


class TreeMeta:
    def __init__(self, **kwargs):
        self.tree_meta = kwargs.get('tree_meta')
        self.tree_tasks:list = kwargs.get('tree_tasks') or []
        self.tree_name = kwargs.get('tree_name')


class TaskMethodMeta:
    def __init__(self, **kwargs):
        self.func_meta = FuncMeta(**kwargs)
        self.bind_config = kwargs.get('bind_config')
        self.bind_obj = kwargs.get('bind_obj')
        self.bind_arg = kwargs.get('bind_arg')
        self.hook_type = kwargs.get('hook_type')
    
    @property
    def func_name(self):
        return self.func_meta.func_name if self.func_meta else None

    @property
    def func_args(self):
        return self.func_meta.func_args if self.func_meta else None

    @property
    def func_kwargs(self):
        return self.func_meta.func_kwargs if self.func_meta else None


class TreeRunMode(Enum):
    # 串行执行任务
    default = 'default'
    # 多线程模式
    worker_mt = 'worker_mt'
    # 多进程模式
    worker_mp = 'worker_mp'


class TreeTaskRunOpts(Enum):
    # asdl tree task node run opts
    # opt_key = (key_name, )

    # 并发执行数量; Default: None, 表示不启动独立工作进程, 即任务先后串联执行
    worker_num = ('worker_num', )

    # 并发执行模式; Enum: process, thread; Default: process
    worker_mode = ('worker_mode', )

    # 数据管道最大hold数据量; default 0, 表示不限制
    max_queue_size = ('max_queue_size', )

    # 任务单元执行结束后是否发送结束命令到下游任务; default True
    send_end_cmd = ('send_end_cmd', )

    # 是否自动清理输入管道数据; default True
    # 当自定义clean_pip_in=False时, 任务函数必须确保输入管道无残留数据, 否则会导致进程无法退出
    # clean_pip_in=False 典型使用场景: 在 after_task 勾子函数将管道残留数据保存到文件中, 便于从文件恢复处理进度
    clean_pip_in = ('clean_pip_in', )

    # 在任务工作进程启动时是否打开 ptvsd 远程调试; default False
    # worker_num大于1时, 只激活第一个工作进程到远程调试, 为避免数据管道数据被未激活调试到进程全部拉取, 建议设置worker_num=1
    remote_debug = ('remote_debug', )

    # 被连接的任务函数以静态方法还是对象方法执行, 可选static, object; default: static
    join_mode = ('join_mode', )

