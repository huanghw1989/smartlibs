import os, inspect

from smart.utils import tuple_fixed_len, dyn_import
from smart.utils.loader import search_by_dotted_pattern

from smart.auto.loader.meta import TaskMethodsGroupMeta
from smart.auto.loader.manage import AutoLoadManage

from smart.auto.__logger import logger_loader as logger


def module_dir(module):
    if hasattr(module, '__file__') and module.__file__:
        return os.path.dirname(module.__file__)
    else:
        return module.__path__._path[0]


class AutoLoader(object):
    def __init__(self):
        self.module_pathes = {}
    
    def __format_load_opts(self, opts):
        if opts is None:
            return {}
            
        return opts

    def load(self, dotted_pattern, opts=None):
        module_name, dotted_path = tuple_fixed_len(dotted_pattern.split('.', 1), 2)
        module = dyn_import(module_name)

        if not inspect.ismodule(module): 
            return

        root_dir = module_dir(module)

        for found_path in search_by_dotted_pattern(root_dir=root_dir, pattern=dotted_path, ignore_name_prefixes = ['__']):
            found_module_path = module_name + '.' + found_path

            logger.debug('AutoLoader load module %s', found_module_path)

            dyn_import(found_module_path)
            self.module_pathes[found_module_path] = self.__format_load_opts(opts)
    
    def group_task_methods(self):
        """获取任务函数(按task_path分组)
        
        Yields:
            tuple -- task_methods:TaskMethodsGroupMeta, load_opts:dict{rename}
        """
        for task_methods in AutoLoadManage.group_task_methods():
            load_opts = self.module_pathes.get(task_methods.task_meta.mod_path)
            if load_opts is None:
                continue
            
            yield task_methods, load_opts