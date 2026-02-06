import os, importlib, glob, inspect, pathlib
from importlib.util import find_spec
from .path import path_join


MAIN_MODULE_NAME = '__main__'


def has_module(path):
    try:

        return find_spec(path)
    except (AttributeError, ModuleNotFoundError):

        return False


def dyn_import(path):
    """ 动态加载
    Example: dyn_import('demo.run_task.TaggingSysData')
    
    Arguments:
        path {str|list|tuple} -- 类路径, 包名通过.分隔

    Raises:
        ModuleNotFoundError: path所在的模块未找到
        AttributeError: path未找到

    Returns:
        any -- path对应项
    """
    if not path:
        return None

    package, *attrs = path.split('.') if isinstance(path, str) else path
    
    # ModuleNotFoundError
    obj = importlib.import_module(package)
    b_find_module = True

    for attr in attrs:
        try_package = package + '.' + attr

        if b_find_module and has_module(try_package):

            obj = importlib.import_module(try_package)
            package = try_package
        else:

            # AttributeError
            obj = getattr(obj, attr)
            b_find_module = False

    return obj


def __file_is_starts_with(file_path, name_prefixes):
    file_base_name = os.path.basename(file_path)

    for name_prefix in name_prefixes:
        if file_base_name.startswith(name_prefix):
            return True
    
    return False


def search_by_dotted_pattern(root_dir, pattern, suffix='.py', ignore_name_prefixes=None):
    file_pattern = pattern.replace('.', '/') + suffix
    search_pattern = os.path.join(root_dir, file_pattern)

    for file_path in glob.glob(search_pattern, recursive=True):

        if not file_path.startswith(root_dir): 
            continue
        
        if ignore_name_prefixes and __file_is_starts_with(file_path, ignore_name_prefixes):
            continue

        relative_path = file_path[len(root_dir):].lstrip('/\\')
        dotted_path = relative_path[:-3].replace('/', '.').replace('\\', '.')

        yield dotted_path


def get_import_path(obj):
    if inspect.ismodule(obj):
        return obj.__name__
    
    if inspect.isfunction(obj):
        pass
    elif not inspect.isclass(obj):
        obj = type(obj)
        
    return obj.__module__ + '.' + (obj.__qualname__ if hasattr(obj, '__qualname__') else obj.__name__)


def get_func_cls_name(func):
    qual_name = getattr(func, '__qualname__')
    func_name = getattr(func, '__name__')
    if not qual_name or qual_name == func_name:
        return None
    cls_name = qual_name[:-len(func_name)-1] if qual_name.endswith('.'+func_name) else None
    return cls_name

def get_func_cls_path(func):
    mod_path = getattr(func, '__module__')
    if not mod_path:
        return None
    cls_name = get_func_cls_name(func)
    return mod_path + '.' + cls_name

class ModulePathUtil:
    @staticmethod
    def get_module_file_path(obj):
        if inspect.ismodule(obj):
            if hasattr(obj, '__file__') and obj.__file__:
                if obj.__package__ == obj.__name__:
                    return os.path.dirname(obj.__file__)
                else:
                    return obj.__file__.rsplit('.', 1)[0]
            
            if not hasattr(obj, '__path__'):
                return None

            mod_path = obj.__path__

            if hasattr(mod_path, '_path'):
                mod_path = mod_path._path

            if isinstance(mod_path, list):
                return mod_path[0]
                
            return mod_path
            
        # if not hasattr(obj, '__module__'):
        #     return None
        
        # mod_path = obj.__module__

        # if resolve_main_module and mod_path == MAIN_MODULE_NAME:
        #     main_module = dyn_import(MAIN_MODULE_NAME)
        #     cwd = os.getcwd()
        #     main_module_path = pathlib.PurePath(main_module.__file__)
        #     main_module_path = main_module_path.relative_to(cwd)
        #     dir_path = str(main_module_path.parent).strip('/\\')

        #     return dir_path.replace('/', '.') + '.' + main_module_path.stem
        
        # return mod_path

    @staticmethod
    def obj_module_dot_path(obj, resolve_main_module=False):
        """获取对象所属的module路径
        """    
        if not hasattr(obj, '__module__'):
            return None
        
        mod_path = obj.__module__

        if resolve_main_module and mod_path == MAIN_MODULE_NAME:
            main_module = dyn_import(MAIN_MODULE_NAME)
            cwd = os.getcwd()
            main_module_path = pathlib.PurePath(main_module.__file__)
            main_module_path = main_module_path.relative_to(cwd)
            dir_path = str(main_module_path.parent).strip('/\\')

            return dir_path.replace('/', '.') + '.' + main_module_path.stem
        
        return mod_path
    
    @staticmethod
    def parent_module(module_path):
        names = module_path.rsplit('.', 1)

        return names[0] if len(names) > 1 else ''
    
    @staticmethod
    def find_module_file_path_by_dot_path(dot_path, root_dir_path=None):
        """查找模块下的文件
        
        Arguments:
            dot_path {str} -- 模块文件路径
        
        Keyword Arguments:
            root_dir_path {str} -- 根文件夹目录 (default: {None})
        
        Returns:
            tuple -- (module_path, file_name)
        """
        if not dot_path:
            return None, None

        if isinstance(dot_path, (list, tuple)):
            module_pathes = dot_path
        else:
            module_pathes = dot_path.split('.')
        
        # sub_mod_dirs = []
        ctx_mod_path, start, end = None, 0, 0

        for i, sub_mod_path in enumerate(module_pathes):
            if not sub_mod_path:
                continue

            dir_path = path_join(root_dir_path, ctx_mod_path, *module_pathes[start:i+1])

            if os.path.exists(dir_path):
                end = i + 1
                continue
            else:
                try:

                    mod_obj = dyn_import(module_pathes[:i+1])
                    ctx_mod_path = ModulePathUtil.get_module_file_path(mod_obj)
                    if ctx_mod_path is None:
                        # build-in模块无路径
                        break
                    start = end = i + 1
                except (ModuleNotFoundError, AttributeError):

                    break
        
        return path_join(ctx_mod_path, os.path.sep.join(module_pathes[start:end])), '.'.join(module_pathes[end:])


class PathLoader:
    _cached_obj = {}

    @staticmethod
    def dyn_import(self, path):
        if path not in PathLoader._cached_obj:
            PathLoader._cached_obj[path] = dyn_import(path)
        
        return PathLoader._cached_obj[path]