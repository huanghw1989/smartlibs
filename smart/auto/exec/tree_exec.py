import inspect, re
import multiprocessing as mp
from smart.auto.exec.task_pod import TaskPod

from smart.utils.loader import dyn_import, get_import_path
from smart.utils.number import safe_parse_int

from smart.auto.constants import Constants
from smart.auto.pip import QueuePip
from smart.auto.meta import TaskMeta, EnumTaskType, TreeTaskRunOpts
from smart.auto.tree import TreeTask, TreeLambdaTask, TreeFuncTask, TreeModuleTask
from smart.auto.exec.fn_chain import FnChain, FnItem
from smart.auto.ctx.tree_context import TreeContext

from smart.auto.__logger import logger


class TreeTaskExecutor:
    def __init__(self, task_class, task_init_args=[], task_init_kwargs={}, 
                context:TreeContext=None, task_meta:TaskMeta=None, run_opts=None):
        self.task_class = task_class
        self.task_meta = task_meta
        self.func_meta = task_meta.task_method_meta if task_meta else None
        self.context = context
        self.__all_task_obj = {}
        self.task_obj:TreeTask = self._new_task_obj(task_class, task_init_args, task_init_kwargs)
        self._run_opts = run_opts

        self.fn_chain = FnChain()
        self.fn_chain.new_block().add_item(
            self._fn_item(task_meta)
        )
        self.task_pod:TaskPod = None

    def _new_task_obj(self, task_class, task_init_args, task_init_kwargs, join_obj=False):
        args = task_init_args
        kwargs = {
            'pip_out_fn': self.pip_fn,
            'context': self.context
        }
        kwargs.update(task_init_kwargs)
        kwargs['task_key'] = self.task_meta.task_key
        
        task_class_path = None
        if isinstance(task_class, str):
            task_class_path = task_class
            task_class = dyn_import(task_class)
        else:
            task_class_path = get_import_path(task_class)
        
        if task_class_path in self.__all_task_obj:
            return self.__all_task_obj[task_class_path]
        
        task_obj = None
        if inspect.ismodule(task_class):
            task_obj = TreeModuleTask(task_class, *args, **kwargs)
        elif inspect.isfunction(task_class):
            if task_class.__name__ == '<lambda>':
                task_obj =  TreeLambdaTask(lambda_func=task_class, *args, **kwargs)
            else:
                task_obj =  TreeFuncTask(run_func=task_class, *args, **kwargs)
        else:
            task_obj = task_class(*args, **kwargs)
        self.__all_task_obj[task_class_path] = task_obj
        if join_obj:
            self.task_obj.join_task(task_obj)
        return task_obj
    
    def all_task_obj(self):
        for task_class_path, task_obj in self.__all_task_obj.items():
            yield task_class_path, task_obj
    
    def __get_run_opt(self, opt:TreeTaskRunOpts, default_val=None):
        key = opt.value[0]
        return (self._run_opts or {}).get(key, default_val)
        
    def pip_fn(self):
        max_queue_size = safe_parse_int(self.__get_run_opt(TreeTaskRunOpts.max_queue_size), 0)

        queue_opts = {}
        if max_queue_size > 0:
            # plus 1 for end_cmd
            max_queue_size = max_queue_size + 1

            if Constants.SEM_VALUE_MAX and max_queue_size > Constants.SEM_VALUE_MAX:
                logger.debug('max_queue_size %s must less then SEM_VALUE_MAX(%s), force reduce it', max_queue_size, Constants.SEM_VALUE_MAX)
                max_queue_size = Constants.SEM_VALUE_MAX

            queue_opts['maxsize'] = max_queue_size

        return QueuePip(queue=mp.Queue(**queue_opts))
    
    def _fn_item(self, task_meta:TaskMeta):
        if not task_meta:
            return None

        run_task_meta:TaskMeta = task_meta.ext_task_meta or task_meta
        method_meta = run_task_meta.task_method_meta

        if method_meta is None:
            logger.warning('Task Method %s is None', task_meta.task_key)
            return None
        
        func_name, args, kwargs = method_meta.func_name, method_meta.func_args or [], method_meta.func_kwargs or {}

        if task_meta.ext_task_meta:
            join_mode = self._run_opts.get('join_mode', Constants.DEFAULT_TASK_JOIN_MODE)
            ext_method_meta = run_task_meta.task_method_meta
            hook_type = ext_method_meta.hook_type if ext_method_meta else None
            if join_mode == 'object':
                task_class = run_task_meta.task_class
                task_dict = run_task_meta.task_dict or {}
                task_init_opts = task_dict.get('init', {})
                task_init_args = task_init_opts.get('args', [])
                task_init_kwargs = task_init_opts.get('kwargs', {}).copy()
                join_task_obj = self._new_task_obj(task_class, task_init_args, task_init_kwargs, join_obj=True)
                func = self.__get_method(join_task_obj, func_name, hook_type=hook_type)
            else:
                func = self.get_static_method(task_meta.ext_task_meta)
                args.insert(0, self.task_obj)
        else:
            hook_type = method_meta.hook_type if method_meta else None
            func = self.__get_method(self.task_obj, func_name, hook_type=hook_type)
        
        # logger.debug('Task %s %s starting, pid=%s', self.task_class, task_meta.task_key, os.getpid())

        fn_item_name = (task_meta.task_key, task_meta.task_class_path or task_meta.task_class)
        fn_item_type = ('hook', hook_type) if hook_type else 'task'

        fn_item = FnItem(
            func, 
            type = fn_item_type,
            name = fn_item_name
        )

        fn_item.bind(*args, **kwargs)

        return fn_item

    def add_join_task_group(self, join_task_list:list):
        if join_task_list:
            fn_block = self.fn_chain.new_block()

            for task_meta in join_task_list:
                fn_block.add_item(
                    self._fn_item(task_meta)
                )

        return self
    
    def __get_method(self, obj, func_name, hook_type=None):
        real_func_name = re.sub(r'\$\d+$', '', func_name)
        fn = getattr(obj, real_func_name)

        return fn
    
    def get_static_method(self, task_meta:TaskMeta):
        task_class = task_meta.task_class
        method_meta = task_meta.task_method_meta
        hook_type = method_meta.hook_type if method_meta else None

        if isinstance(task_class, str):
            task_class = task_meta.task_class = dyn_import(task_class)

        if task_meta.task_type in (EnumTaskType.func_task,):
            return task_class
        else:
            return self.__get_method(task_class, task_meta.func_name, hook_type=hook_type)
    
    def run_hook(self, hook_type, context:TreeContext=None):
        if context:
            context.run_stage = hook_type

        self.fn_chain.run_chain(
            fn_filter=lambda fn_item: fn_item.fn_type == ('hook', hook_type)
        )

    def exec_fn(self, worker_num=None, worker_mode=None, send_end_cmd=True, 
            clean_pip_in=True, remote_debug=False, restart=None, **kwargs) -> TaskPod:
        task_pod = self.task_pod = TaskPod(
            context = self.context,
            task_meta = self.task_meta,
            fn_chain = self.fn_chain,
            worker_mode = worker_mode,
            worker_num = worker_num,
            restart = restart, 
            **kwargs
        )

        task_pod.start(
            send_end_cmd=send_end_cmd,
            clean_pip_in=clean_pip_in,
            remote_debug=remote_debug
        )
        return task_pod