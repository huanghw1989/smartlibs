import time, sys

from smart.utils import dyn_import, list_safe_iter, \
                dict_safe_get, dict_deep_merge, \
                func_safe_bind, AppEnv

from smart.auto.constants import Constants
from smart.auto.tree import TreeContext
from smart.auto.parser.tools import is_private_key, parse_task_exp
from smart.auto.parser.task import TaskMetaParser
from smart.auto.exec.tree_exec import TreeTaskExecutor
from smart.auto.exec.tree_pod import TreePod
from smart.auto.meta import TaskMeta, TreeTaskMeta, TreeMeta, TreeRunMode
from smart.auto.ctx.runner_context import WithAutoRunner

from smart.auto.__logger import logger


class AutoRunner:
    def __init__(self, run_obj, debug_log=None, lazy_load=True):
        self.run_obj = run_obj
        self.lazy_load = lazy_load
        config_dict = run_obj.get('configs') or {}
        
        if debug_log is not None:
            config_dict['debug_log'] = debug_log

        self.context = TreeContext(configs=config_dict)
        
        self.tree_map = self.__parse_trees(run_obj)
        self.task_meta_parser = TaskMetaParser(run_obj, lazy_load=lazy_load)

    def __parse_trees(self, run_obj):
        tree_map = {}
        tree_run_obj = run_obj.get('trees') or {}

        for tree_name, tree_meta_dict in tree_run_obj.items():
            tree_map[tree_name] = tree_meta_dict

        return tree_map
    
    def __get_tree(self, tree_name) -> TreeMeta:
        if tree_name not in self.tree_map:
            raise AttributeError('tree ' + tree_name + ' no found')

        tree_meta_dict = self.tree_map[tree_name]
        tree_tasks = []

        for task_key, exec_opts in tree_meta_dict.items():

            if is_private_key(task_key): continue

            exec_opts = exec_opts or {}
            task_meta = self.task_meta_parser.parse_task_meta(task_key)
            tree_task_meta = TreeTaskMeta(
                task_meta=task_meta, exec_opts=exec_opts)

            self.__init_task_executor(task_meta, 
                joins=exec_opts.get('join', []),
                run_opts=exec_opts)
            tree_tasks.append(tree_task_meta)

        tree = TreeMeta(
            tree_tasks = tree_tasks,
            tree_meta = tree_meta_dict,
            tree_name = tree_name,
        )
        return tree

    def __bind_config(self, config_keys, ori_kwargs=None):
        if not config_keys: return ori_kwargs
        configs = self.run_obj.get('configs') or {}
        extra_kwargs = {}
        for dotted_cfg_key in list_safe_iter(config_keys):
            if not dotted_cfg_key: continue
            kwargs = dict_safe_get(configs, dotted_cfg_key.split('.'))
            if isinstance(kwargs, dict):
                extra_kwargs.update(kwargs)
        if ori_kwargs is None:
            return extra_kwargs
        return {**extra_kwargs, **ori_kwargs}

    def __resolve_run_opts(self, task_meta:TaskMeta, run_opts:dict={}):
        if task_meta.ext_task_meta:
            method_meta = task_meta.ext_task_meta.task_method_meta 
        else:
            method_meta = task_meta.task_method_meta 

        # 配置绑定到目标函数参数
        bind_config = run_opts.get('bind_config') or method_meta.bind_config
        func_kwargs = self.__bind_config(bind_config, method_meta.func_kwargs)

        # 绑定函数对象到目标函数参数, 并注入配置到函数对象
        bind_obj = dict_deep_merge(method_meta.bind_obj, run_opts.get('bind_obj')) or {}
        bind_obj_kwargs = {}
        for arg_name, obj_opt in bind_obj.items():
            if not arg_name or not obj_opt: continue
            obj_path, obj_config_keys = obj_opt.get('path'), obj_opt.get('config')
            if not obj_path: continue
            arg_obj = dyn_import(obj_path)
            obj_config = self.__bind_config(obj_config_keys)
            if obj_config:
                arg_obj = func_safe_bind(arg_obj, kwargs=obj_config)
            bind_obj_kwargs[arg_name] = arg_obj
        
        # 绑定参数
        bind_arg_kwargs = method_meta.bind_arg or {}
        if run_opts.get('bind_arg'):
            bind_arg_kwargs.update(run_opts.get('bind_arg'))

        method_meta.func_meta.func_kwargs = {**func_kwargs, **bind_arg_kwargs, **bind_obj_kwargs}

    def __init_task_executor(self, task_meta:TaskMeta, joins:list=[], bind_config:list=[], run_opts:dict={}):
        main_task_key_info = task_meta.task_key_info

        task_dict = task_meta.task_dict or {}
        # def_dict = task_dict.get('def') or {}
        task_init_opts = task_dict.get('init', {})
        task_init_kwargs = task_init_opts.get('kwargs', {}).copy()

        self.__resolve_run_opts(task_meta, run_opts=run_opts)

        # 创建任务执行器
        executor = TreeTaskExecutor(
            task_class = task_meta.task_class, 
            task_init_args = task_init_opts.get('args', []), 
            task_init_kwargs = task_init_kwargs, 
            context = self.context,
            task_meta = task_meta,
            run_opts = run_opts,
        )

        # 设置连接函数
        if joins:
            for join_dict in joins:
                join_task_list = []

                for join_name, join_opts in join_dict.items():
                    join_task_meta = self.task_meta_parser.parse_join_task_meta(main_task_key_info, join_name)
                    self.__resolve_run_opts(join_task_meta, run_opts=join_opts)
                    join_task_list.append(join_task_meta)

                executor.add_join_task_group(join_task_list)

        task_meta.task_executor = executor
        task_meta.task_obj = executor.task_obj

        for _, _task_obj in executor.all_task_obj():
            if isinstance(_task_obj, WithAutoRunner):
                _task_obj.auto_runner = self

        return task_meta
        
    def __init_tree(self, tree:TreeMeta):
        task_map = {}
        for tree_task in tree.tree_tasks:
            task_map[tree_task.task_meta.task_key] = tree_task
        task_depends = set()
        
        def __get_task(task_key) -> TreeTaskMeta:
            if task_key not in task_map:
                raise AttributeError('task_key ' + task_key + ' no in trees')
            return task_map[task_key]

        def __iter_dependance(tree_task: TreeTaskMeta):
            exec_opts = tree_task.exec_opts or {}
            task_meta = tree_task.task_meta
            task_key = task_meta.task_key
            prev_task_key = exec_opts.get('prev')
            if prev_task_key:
                yield prev_task_key, __get_task(prev_task_key), task_key, tree_task
            for next_task_key in list_safe_iter(exec_opts.get('next')):
                if next_task_key:
                    yield task_key, tree_task, next_task_key, __get_task(next_task_key)
        
        use_worker = False
        use_worker_mp = False
        for tree_task in tree.tree_tasks:
            tree_task:TreeTaskMeta
            for prev_task_key, prev_task_meta, next_task_key, next_task_meta in __iter_dependance(tree_task):
                if (prev_task_key, next_task_key) not in task_depends:
                    # 设置任务依赖关系
                    logger.debug('Task Dependance: %s -> %s', prev_task_key, next_task_key)
                    prev_task_meta.task_meta.task_obj.next(
                        next_task_meta.task_meta.task_obj
                    )
                    task_depends.add((prev_task_key, next_task_key))
            # 设置运行模式
            exec_opts = tree_task.exec_opts or {}
            if exec_opts.get('worker_num'):
                use_worker = True
                worker_mode = exec_opts.get('worker_mode')
                if worker_mode is None:
                    worker_mode = exec_opts['worker_mode'] = Constants.DEFAULT_WORKER_MODE
                if worker_mode != 'thread':
                    use_worker_mp = True
        
        if use_worker_mp:
            self.context.run_mode = TreeRunMode.worker_mp
        elif use_worker:
            self.context.run_mode = TreeRunMode.worker_mt
        else:
            self.context.run_mode = TreeRunMode.default

    def start_task(self, task_exp):
        task_key, run_opts = parse_task_exp(task_exp)
        task_meta = self.task_meta_parser.parse_task_meta(task_key)

        self.__init_task_executor(task_meta, 
            joins=run_opts.get('join'),
            run_opts=run_opts)
        
        context = self.context
        context.run_mode = TreeRunMode.default
        task_executor:TreeTaskExecutor = task_meta.task_executor

        # Execute hook before_task
        task_executor.run_hook('before_task', context=context)

        # Execute Task
        task_pod = task_executor.exec_fn()

        # Execute hook after_task
        task_executor.run_hook('after_task', context=context)
    
    def is_tree_done(self, tree: TreeMeta):
        for tree_task_meta in tree.tree_tasks:
            exec_opts = tree_task_meta.exec_opts or {}
            task_executor:TreeTaskExecutor = tree_task_meta.task_executor
            if not task_executor.is_done(exec_opts.get('worker_num')):
                return False
        return 

    def start_tree(self, tree_name):
        tree = self.__get_tree(tree_name)
        self.__init_tree(tree)

        context = self.context

        # Init store
        ctx_store_type = type(context.store)
        logger.debug('context run_mode: %s, %s', context.run_mode, ctx_store_type)

        pod = TreePod(
            tree_name=tree_name,
            tree=tree,
            context=context
        )
        pod.start()
        pod.join()
        return pod
    
    def start(self, name, default_ns='tree'):
        time_begin = time.monotonic()
        args = name.split(':', 1)
        type = args.pop(0) if len(args) > 1 else default_ns

        if type == 'task':
            self.start_task(*args)
        else:
            self.start_tree(*args)

        time_during = time.monotonic() - time_begin
        logger.debug('%s took %f seconds', name, time_during)


            