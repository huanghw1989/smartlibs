from smart.utils import tuple_fixed_len, list_safe_iter
from smart.utils.loader import PathLoader

from smart.auto.base import BaseTask
from smart.auto.meta import TaskMeta, TaskMethodMeta, EnumTaskType, TaskKeyInfo
from smart.auto.parser.tools import TaskFinder

from smart.auto.__logger import logger


class TaskKeyFullInfo(TaskKeyInfo):
    def __init__(self, **kwargs):
        TaskKeyInfo.__init__(self, **kwargs)
        self.task_name = kwargs.get('task_name')
        self.task_class = kwargs.get('task_class')
        self.task_class_path = kwargs.get('task_class_path')
        self.task_dict = kwargs.get('task_dict')


class TaskMetaParser:
    def __init__(self, run_obj:dict, lazy_load=True):
        self.run_obj = run_obj
        self.lazy_load = lazy_load
        self.task_finder = TaskFinder(
            run_obj.get('tasks', {})
        )
    
    def parse_task_key_info(self, task_key:str) -> TaskKeyFullInfo:
        task_key_info = TaskKeyFullInfo(
            full_key = task_key
        )
        task_key_base, ext_func_key = tuple_fixed_len(task_key.split('.@', 1), 2)

        if ext_func_key:

            func_key_type = '@'
            cls_key = task_key_base
            func_name, func_name_tail = TaskKeyInfo.parse_func_name_tail(ext_func_key)
            task_info_tuple, task_name = self.__find_task_info_tuple(cls_key)
        else:

            func_key_type = None
            task_key_base, func_name_tail = TaskKeyInfo.parse_func_name_tail(task_key_base)

            cls_key, func_name = tuple_fixed_len(task_key_base.rsplit('.', 1), 2)
            task_info_tuple, task_name = self.__find_task_info_tuple(cls_key)

            if (not task_name) and task_key_base != cls_key:
                task_info_tuple, task_name = self.__find_task_info_tuple(task_key_base)

                if task_name:
                    cls_key = task_key_base
                    func_name = None
        
        if task_info_tuple:
            task_class, task_class_path, task_dict, *_ = task_info_tuple
            task_key_info.task_name = task_name
            task_key_info.task_class = task_class
            task_key_info.task_class_path = task_class_path
            task_key_info.task_dict = task_dict

        task_key_info.cls_key = cls_key
        task_key_info.func_name = func_name
        task_key_info.func_name_tail = func_name_tail
        task_key_info.func_key_type = func_key_type

        return task_key_info
    
    def __find_task_info_tuple(self, task_name):
        task_dict, found_name = self.task_finder.find_task_dict(task_name)

        if task_dict is not None:
            task_class, task_class_path = task_dict.get('class'), None
            if not task_class:
                return None, None

            if isinstance(task_class, str):
                task_class_path = task_class

            if not self.lazy_load and task_class_path:
                task_class = PathLoader.dyn_import(task_class_path)

            return (task_class, task_class_path, task_dict), found_name
        
        return None, None
    
    def parse_task_meta(self, task_key = None) -> TaskMeta:
        task_key_info = self.parse_task_key_info(task_key)

        func_name, task_type, ext_task_meta = None, None, None
        task_class, task_class_path, task_dict = None, None, None

        task_cls_key = task_key_info.cls_key
        task_name = task_key_info.task_name

        if task_name is None:
            module_path, task_name = tuple_fixed_len(task_cls_key.rsplit('.', 1), 2, left_pad=True)
        else:
            # 存在任务字典
            module_path = None
            task_class = task_key_info.task_class
            task_class_path = task_key_info.task_class_path
            task_dict = task_key_info.task_dict

        if task_key_info.func_is_ext:

            task_type = EnumTaskType.ext
            ext_task_meta = self.parse_task_meta(task_key_info.func_key)
        else:

            func_name = task_key_info.func_name

            if func_name is None:
                 # It's func_task
                 task_type = EnumTaskType.func_task
    
        if module_path:
            
            # 动态加载任务
            try:
                task_class_path = module_path + '.' + task_name
                task_class = PathLoader.dyn_import(module_path)
                task_dict = {}

                if (not isinstance(task_class, BaseTask)) and func_name:
                    task_class = getattr(task_class, func_name)
                    task_class_path += '.' + func_name
                    task_type = EnumTaskType.func_task
            except Exception as e:
                logger.debug('TaskMetaParser.parse_task_meta dyn_import error: %s', e)
                raise AttributeError('task ' + task_name + ' no found')

        if not task_key_info.func_is_ext:
            task_method_meta = self.parse_task_method_meta(task_dict, func_name or 'start')
        else:
            task_method_meta = None
        
        if task_class is None and task_class_path is None:
            raise ValueError('Task {} not found (key:{})'.format(task_name, task_key))

        task_meta = TaskMeta(
            task_class=task_class,
            task_class_path=task_class_path,
            task_dict=task_dict,
            task_name=task_name,
            task_key_info=task_key_info,
            task_type=task_type,
            func_name=func_name,
            task_method_meta=task_method_meta,
            ext_task_meta=ext_task_meta,
        )

        return task_meta
    
    def parse_join_task_meta(self, main_key_info: TaskKeyInfo, join_key) -> TaskMeta:
        join_task_key = main_key_info.cls_key + '.' + join_key
        
        return self.parse_task_meta(join_task_key)


    def parse_task_method_meta(self, task_dict:dict, func_name:str) -> TaskMethodMeta:
        """解析任务函数

        Arguments:
            task_dict {dict} -- 任务字典
            func_name {str} -- 任务函数名称

        Returns:
            TaskMethodMeta -- 任务函数元数据
        """
        if task_dict is None:
            return None
            
        func_run_opts = (task_dict.get('def') or {}).get(func_name) or {}

        return TaskMethodMeta(
            func_name = func_name,
            func_args = func_run_opts.get('args', []),
            func_kwargs = func_run_opts.get('kwargs', {}),
            bind_config = func_run_opts.get('bind_config', []),
            bind_obj = func_run_opts.get('bind_obj', {}),
            bind_arg = func_run_opts.get('bind_arg', {}),
            hook_type = func_run_opts.get('hook_type', {}),
        )