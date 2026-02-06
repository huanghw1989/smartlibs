import inspect, os, glob
import functools

# from smart.utils import dyn_import
from smart.utils.loader import dyn_import, ModulePathUtil
from smart.utils.dot_path import cast_dot_pattern_to_file_pattern

from .module_manage import ModuleManage, ModuleClsType
from .route_manage import RouteManage
from .interceptor import BaseInterceptor
from .interceptor_manage import InterceptorManage

from ..__logger import logger_rest


def search_py_by_dotted_pattern(root_dir, pattern):
    if not pattern:
        yield from []
    
    file_pattern = cast_dot_pattern_to_file_pattern(pattern)
    file_pattern += '.py'
    search_pattern = os.path.join(root_dir, file_pattern)

    for file_path in glob.glob(search_pattern, recursive=True):
        if not file_path.startswith(root_dir): 
            continue

        relative_path = file_path[len(root_dir):].lstrip('/\\')
        if relative_path[:2] in ('./', '.'+os.path.sep):
            relative_path = relative_path[2:]

        dotted_path = relative_path[:-3].replace('/', '.').replace('\\', '.')

        yield dotted_path


class BootOpts:
    def __init__(self):
        self.crond_enable = False
        self.crond_run_in_process = False


class BootConfig:
    def __init__(self, app_root='.'):
        self.opts = BootOpts()
        self.app_root = app_root
        self.module_m = ModuleManage()
        self.interceptor_m = InterceptorManage()
        self.route_m = RouteManage(module_m=self.module_m)
    
    def __scan_module(self, boot_clazz, pattern, on_found=None):
        if inspect.isclass(boot_clazz) and issubclass(boot_clazz, Bootable):
            logger_rest.debug('BootConfig scan module: %s', pattern)

            boot_clazz.boot_config = self
            app_root = os.path.join(os.path.dirname(inspect.getfile(boot_clazz)), self.app_root)
            app_abs_root = os.path.abspath(app_root)

            module_prefix = ModulePathUtil.parent_module(
                ModulePathUtil.obj_module_dot_path(boot_clazz, resolve_main_module=True)
            )

            logger_rest.debug('BootConfig root dir: %s, context module: %s', app_abs_root, module_prefix)

            if module_prefix: 
                module_prefix = module_prefix + '.'
            
            logger_rest.debug('scan module %s, context_path is %s', pattern, app_abs_root)

            if pattern:
                for dotted_path in search_py_by_dotted_pattern(app_abs_root, pattern):
                    dotted_path = module_prefix + dotted_path
                    module_obj = self.module_m.add_module(dotted_path)

                    if on_found:
                        on_found(dotted_path, module_obj)
        else:
            logger_rest.warning("BootConfig.scan_module ignore not Bootable class %s", boot_clazz)
    
    def module(self, pattern):
        def decorator(clazz):
            self.__scan_module(clazz, pattern)
            return clazz

        return decorator
    
    def service(self, pattern):
        def decorator(clazz):
            self.__scan_module(clazz, pattern)
            return clazz

        return decorator
    
    def __null_decorator(self, clazz):
        return clazz
    
    def crond(self, enable=True, run_in_process=False):
        self.opts.crond_enable = enable
        self.opts.crond_run_in_process = run_in_process
        
        return self.__null_decorator
    
    def interceptor(self, priority=10):
        def decorator(clazz):
            self.interceptor_m.add_interceptor(clazz, priority=priority)
            return clazz
        
        return decorator
    
    def init(self):
        self.route_m.init()


class Bootable:
    @property
    def boot_config(self) -> BootConfig:
        return getattr(self, '_boot_config', None)

    @boot_config.setter
    def boot_config(self, config:BootConfig):
        setattr(self, '_boot_config', config)
