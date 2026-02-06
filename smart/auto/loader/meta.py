import typing

from smart.auto.base import BaseTask


class MethodMeta:
    def __init__(self, **kwargs):
        self.mod_path = kwargs.get('mod_path')
        self.cls_name = kwargs.get('cls_name')
        self.func_name = kwargs.get('func_name')
        self.func_config = kwargs.get('func_config')
        self.hook_type = kwargs.get('hook_type')

    @property
    def cls_path(self):
        return '.'.join(filter(None, (
            self.mod_path, self.cls_name
        )))

    @property
    def func_path(self):
        return '.'.join(filter(None, (
            self.mod_path, self.cls_name, self.func_name
        )))
    
    @staticmethod
    def create(func:callable):
        qual_name, func_name, mod_path = func.__qualname__, func.__name__, func.__module__
        cls_name = qual_name[:-len(func_name)-1] if qual_name.endswith('.'+func_name) else None
        return MethodMeta(
            mod_path = mod_path,
            cls_name = cls_name,
            func_name = func_name,
        )


class TaskMeta:
    def __init__(self, **kwargs):
        self.mod_path = kwargs.get('mod_path')
        self.cls_name = kwargs.get('cls_name')
        self.task_name = kwargs.get('task_name')
        self.task_cls = kwargs.get('task_cls')
        self.task_type = kwargs.get('task_type')
        self.task_alias = kwargs.get('task_alias')

    @property
    def cls_path(self):
        return '.'.join(filter(None, (
            self.mod_path, self.cls_name
        )))

    @staticmethod
    def create(clazz: BaseTask):
        mod_path, cls_name = clazz.__module__, clazz.__name__
        return TaskMeta(
            mod_path = mod_path,
            cls_name = cls_name,
            task_cls = clazz
        )
    
    @staticmethod
    def create_func_task(func: callable, func_type='func'):
        mod_path, cls_name = func.__module__, func.__qualname__
        return TaskMeta(
            mod_path = mod_path,
            cls_name = cls_name,
            task_cls = func,
            task_type = func_type,
        )


class TaskMethodsGroupMeta:
    def __init__(self, task_meta:TaskMeta=None, task_methods = None, bind_objs = None, package_ns=None, **kwargs):
        self.task_meta = task_meta
        # AutoLoad.method / AutoLoad.func_task 装饰器创建的 MethodMeta
        self.task_methods:typing.List[MethodMeta] = task_methods
        # AutoLoad.bind_obj 装饰器创建的 ArgMethodMeta
        self.bind_objs:typing.List[ArgMethodMeta] = bind_objs
        # package namespace
        self.package_ns = package_ns
    
    @property
    def cls_path(self):
        return self.task_meta.cls_path if self.task_meta else None


class ArgMethodMeta:
    def __init__(self, method_meta:MethodMeta=None, **kwargs):
        self.method_meta = method_meta
        self.arg_config = kwargs.get('arg_config')
        self.arg_val = kwargs.get('arg_val')
        self.arg_name = kwargs.get('arg_name')
        self.arg_path = kwargs.get('arg_path')

    @property
    def task_path(self):
        if not self.method_meta: return None
        return self.method_meta.cls_path if self.method_meta.cls_name else self.method_meta.func_path


class BindableFunc:
    def __init__(self, func: callable):
        self.__func__ = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__bind_objs = []
    
    def bind_obj(self, func:typing.Union[callable, str], config_keys:list):
        """绑定函数参数
        
        Arguments:
            func {typing.Union[callable, str]} -- function or dotted_func_path
            config_keys {list} -- [description]
        """
        self.__bind_objs.append((func, config_keys))
    
    def __call__(self, *args, **kwargs):
        return self.__func__(self.__self__, *args, **kwargs)