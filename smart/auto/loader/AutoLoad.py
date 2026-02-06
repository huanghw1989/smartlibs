import inspect, typing

from smart.utils import list_safe_iter
from smart.utils.loader import get_import_path
from smart.utils.tuple import iter_fixed_len

from smart.auto.base import BaseTask
from smart.auto.tree import TreeFuncTask
from smart.auto.loader.TaskHook import TaskHook
from smart.auto.loader.meta import MethodMeta, TaskMeta, ArgMethodMeta
from smart.auto.loader.manage import AutoLoadManage

from smart.auto.__logger import logger_loader as logger


class AutoLoad(object):
    def __init__(self):
        self.hook = TaskHook()

    def task(self, name, alias=None):
        """自动载入任务类到 auto.yml 配置, 在BaseTask子类添加本装饰器
        
        Arguments:
            name {str} -- 任务名称
            alias {list|str} -- 任务别名
        """
        def decorator(clazz:BaseTask):
            if inspect.isclass(clazz) and issubclass(clazz, BaseTask):
                setattr(clazz, '__task_name__', name)
                # setattr(clazz, '__task_methods__', [])
                task_meta = TaskMeta.create(clazz)
                task_meta.task_name = name
                task_meta.task_alias = alias
                AutoLoadManage.all_task.append(task_meta)
                logger.debug('AutoLoad task %s: %s', name, clazz)
            else:
                logger.warning('AutoLoad task must be subclass of BaseTask: %s', clazz)

            return clazz
            
        return decorator

    def method(self, config:typing.Union[list, str]=[]):
        """自动载入方法到 auto.yml 配置, 在BaseTask子类的方法添加本装饰器
        
        Keyword Arguments:
            config {typing.Union[list, str]} -- 绑定配置 (default: {[]})
        """
        def decorator(func:callable):
            meta = MethodMeta.create(func)
            meta.func_config = list(filter(None, list_safe_iter(config)))
            AutoLoadManage.all_method.append(meta)

            logger.debug('AutoLoad method %s %s', meta.cls_path, func)

            return func

        return decorator
    
    def func_task(self, name=None, config=[]):
        """将目标函数载入到Task节点
        
        执行任务时将使用TreeFuncTask嵌套目标函数执行 (即目标函数调用时, 首参数为TreeFuncTask实例)
        
        Keyword Arguments:
            name {str} -- 任务名, 为空时使用函数名作为任务名 (default: {None})
            config {list} -- 绑定配置 (default: {[]})
        
        Returns:
            callable -- 装饰器, 不会嵌套目标函数
        """
        def decorator(func:callable):
            if inspect.isfunction(func):
                _name = name or func.__name__
                setattr(func, '__task_name__', _name)
                task_meta = TaskMeta.create_func_task(func)
                task_meta.task_name = _name
                AutoLoadManage.all_task.append(task_meta)

                method_meta = MethodMeta(
                    mod_path = task_meta.mod_path,
                    cls_name = task_meta.cls_name,
                    func_name = None,
                    func_config = list(filter(None, list_safe_iter(config)))
                )
                AutoLoadManage.all_method.append(method_meta)
                logger.debug('AutoLoad func_task %s: %s', _name, func)

            return func

        return decorator
    
    def module_task(self, path:str, name=None, alias=None):
        """自动载入module任务类到 auto.yml 配置
        
        Arguments:
            path {str} -- module dotted_path

        Keyword Arguments:
            name {str} -- 任务名, 为空时使用module名作为任务名 (default: {None})
            alias {list|str} -- 任务别名 (default: {None})
        """
        pkg_path, cls_name = iter_fixed_len(path.rsplit('.', 1), 2, pad_val='', left_pad=True)
        task_name = name or cls_name

        task_meta = TaskMeta(
            mod_path = path,
            cls_name = None,
            task_name = task_name,
            task_alias = alias,
            task_type = 'module'
        )
        AutoLoadManage.all_task.append(task_meta)
        logger.debug('AutoLoad module_task %s: %s', task_name, path)
    
    def set_pkg_namespace(self, package, namespace):
        logger.debug('AutoLoad set_pkg_namespace %s -> %s', package, namespace)
        AutoLoadManage.package_ns_map[package] = namespace
    
    def bind_obj(self, obj, config=[], arg_name=None):
        """将arg绑定到任务函数的参数

        注意: 
        当arg_name为空时，缺省为 arg.__name__, 非变量名! 
        装饰到非任务函数不会产生作用!
        
        示例:
        import numpy as np

        错误写法:
        @auto_load.bind_obj(np)
        def foo(np):
        
        正确写法1: 
        @auto_load.bind_obj(np)
        def foo(numpy):
        
        正确写法2:
        @auto_load.bind_obj(np, arg_name='np'):
        def foo(np):
        
        Arguments:
            obj {callable|str} -- callable or dotted_func_path
        
        Keyword Arguments:
            config {list} -- arg的参数绑定配置 (default: {[]})
            arg_name {str} -- 绑定目标函数的参数名, 缺省为 arg.__name__ (default: {None})
        
        Returns:
            callable -- 装饰器, 不会嵌套目标函数
        """
        def decorator(func:callable):
            nonlocal arg_name

            method_meta = MethodMeta.create(func)
            arg_config = list(filter(None, list_safe_iter(config)))
            arg_path = obj if isinstance(obj, str) else get_import_path(obj)

            if arg_name is None:
                arg_name = arg_path.rsplit('.', 1)[-1]

            arg_meta = ArgMethodMeta(
                method_meta = method_meta,
                arg_config = arg_config,
                arg_val = obj,
                arg_name = arg_name,
                arg_path = arg_path,
            )
            AutoLoadManage.all_bind_obj.append(arg_meta)

            return func
            
        return decorator