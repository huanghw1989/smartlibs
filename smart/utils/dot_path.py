import re, pathlib, os

from smart.utils import path_join, tuple_fixed_len
from smart.utils.loader import ModulePathUtil
from smart.utils.path import path_resolve


class DotPathContext:
    def __init__(self, ctx_dotted_dir=None, ctx_file_dir=None):
        self.ctx_file_dir = ctx_file_dir
        self.__ctx_dotted_dir = ctx_dotted_dir
        self.__ctx_dotted_dir_parts =  None
    
    @property
    def ctx_dotted_dir(self):
        return self.__ctx_dotted_dir
    
    @ctx_dotted_dir.setter
    def ctx_dotted_dir(self, ctx_dotted_dir):
        self.__ctx_dotted_dir = ctx_dotted_dir
        self.__ctx_dotted_dir_parts =  None
    
    @property
    def ctx_dotted_dir_parts(self):
        if not self.__ctx_dotted_dir:
            return None

        if self.__ctx_dotted_dir_parts is None:
            self.__ctx_dotted_dir_parts = self.__ctx_dotted_dir.split('.')
        
        return self.__ctx_dotted_dir_parts

    def resolve_dotted_path(self, dotted_path):
        if any((not dotted_path, not isinstance(dotted_path, str), not self.ctx_dotted_dir)):
            return dotted_path
        
        ctx_dotted_dir = self.ctx_dotted_dir
        ctx_dotted_dir_parts = self.ctx_dotted_dir_parts

        if dotted_path == '.':
            return ctx_dotted_dir
        
        match = re.match(r'^\.+', dotted_path)

        if match:
            parent_lv = len(match.group())

            if parent_lv > len(ctx_dotted_dir_parts) + 1:
                # 相对路径溢出
                return None
            
            return '.'.join((
                *ctx_dotted_dir_parts[:len(ctx_dotted_dir_parts)-parent_lv+1],
                dotted_path[parent_lv:]
            ))
        
        return dotted_path

    def resolve_file_path(self, file_path:str):
        return path_resolve(file_path, context_dir=self.ctx_file_dir)


class DotPath:
    def __init__(self, ctx:DotPathContext=None, file_suffix=None):
        self.__ctx = ctx
        self.file_suffix = file_suffix
        self.__dotted_path = None
        self.__file_path = None
        self.__as_context = None
    
    @staticmethod
    def create(dotted_path, file_suffix=None) -> 'DotPath':
        path = DotPath(ctx=None, file_suffix=file_suffix)
        path.dotted_path = dotted_path
        
        return path
    
    def _dotted_path2file_path(self, dotted_path):
        if not dotted_path:
            return None

        _module_path, file_name = tuple_fixed_len(dotted_path.rsplit('.', 1), fix_len=2, left_pad=True)

        if _module_path:
            mod_file_path, file_name_prefix = ModulePathUtil.find_module_file_path_by_dot_path(_module_path)

            if file_name_prefix:
                file_name = file_name_prefix + '.' + file_name
        else:
            mod_file_path = None
        
        file_path = path_join(mod_file_path, file_name + self.file_suffix)

        return file_path
    
    @property
    def ctx(self):
        if self.__ctx is None:
            self.__ctx = DotPathContext()
        
        return self.__ctx
    
    @property
    def file_path(self):
        if self.__file_path is None:
            if self.__dotted_path:
                self.__file_path = self._dotted_path2file_path(self.__dotted_path)
        
        return self.__file_path

    @property
    def dotted_path(self):
        return self.__dotted_path
    
    @dotted_path.setter
    def dotted_path(self, dotted_path):
        self.__dotted_path = self.ctx.resolve_dotted_path(dotted_path)
        self.__file_path = None
        self.__as_context = None
    
    def as_context(self) -> DotPathContext:
        if not self.__as_context:
            dotted_path = self.dotted_path

            if not dotted_path:
                file_dir, dotted_dir = None, None
            else:
                _file_path = pathlib.PurePath(self.file_path)
                file_dir = str(_file_path.parent)
                file_name = _file_path.stem

                if dotted_path.endswith(file_name):
                    dotted_dir = dotted_path[:-len(file_name)-1]
                else:
                    dotted_dir = dotted_path.rsplit('.', 1)[0]

            self.__as_context = DotPathContext(
                dotted_dir,
                file_dir
            )
        
        return self.__as_context
    
    def join_path(self, dotted_path:str) -> 'DotPath':
        join_dotted_path = DotPath(
            self.as_context(), self.file_suffix
        )

        join_dotted_path.dotted_path = dotted_path

        return join_dotted_path
    
    def resolve_dotted_path(self, dotted_path):
        return self.as_context().resolve_dotted_path(dotted_path)
    
    def resolve_file_path(self, file_path):
        return self.as_context().resolve_file_path(file_path)


def resolve_dot_path(dot_path, ctx_dotted_dir=None):
    _ctx = DotPathContext(ctx_dotted_dir = ctx_dotted_dir)
    return _ctx.resolve_dotted_path(dot_path)


def cast_dot_pattern_to_file_pattern(dot_pattern):
    """点路径pattern转为文件路径pattern

    例如:
        .* -> ./* or .\\*(windows)
        ..* -> ../*
        ...* => ../../*

    Args:
        dot_pattern (str): 点路径pattern

    Returns:
        str: 文件路径pattern
    """
    if not dot_pattern:
        return None

    file_pattern = ''
    is_begin = True
    prepend_relative = False

    for i in range(len(dot_pattern)):
        if dot_pattern[i] == '.':
            if is_begin:
                if i == 0:
                    prepend_relative = True
                else:
                    file_pattern += '..' + os.path.sep
                if i == 1:
                    prepend_relative = False
            else:
                file_pattern += os.path.sep
        else:
            file_pattern += dot_pattern[i]
            is_begin = False
    
    if prepend_relative:
        file_pattern = '.' + os.path.sep + file_pattern
    
    return file_pattern