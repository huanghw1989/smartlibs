from enum import Enum
import inspect

from smart.utils import dyn_import, dict_get_or_set

from ..__logger import logger_rest


class ModuleClsType(Enum):
    service = 'service'
    interceptor = 'interceptor'


class ModuleManage():
    __imported_module = {}
    __mod_cls_group_map = {}

    def __init__(self):
        self.all_module = {}

    def add_module(self, module_path):
        if module_path in self.__imported_module:
            module_obj = self.__imported_module[module_path]
        else:
            logger_rest.debug('ModuleManage add module %s', module_path)
            module_obj = self.__imported_module[module_path] = dyn_import(module_path)
        
        self.all_module[module_path] = module_obj

        return module_obj
    
    @staticmethod
    def __add_mod_cls_type(module_path, cls_type:ModuleClsType, clazz):
        clazz_list = dict_get_or_set(ModuleManage.__mod_cls_group_map, [(module_path, cls_type)], [])
        clazz_list.append(clazz)
    
    @staticmethod
    def register_class(clazz, cls_type:ModuleClsType):
        if not inspect.isclass(clazz):
            return 
        module_path = clazz.__module__
        ModuleManage.__add_mod_cls_type(module_path, cls_type, clazz)
        
        return module_path