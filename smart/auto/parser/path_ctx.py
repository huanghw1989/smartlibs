import os

from smart.utils.dot_path import DotPath
from smart.utils.path import path_resolve


class PathContext:
    def __init__(self, file_path=None, dot_path:DotPath=None):
        if dot_path is not None:
            if file_path is None:
                file_path = dot_path.file_path
        
        self.__file_path = file_path
        self.__dot_path:DotPath = dot_path
    
    @property
    def file_path(self):
        if self.__file_path is None:
            if self.__dot_path is not None:
                self.__file_path = self.__dot_path.file_path
        
        return self.__file_path
    
    @property
    def dot_path(self) -> DotPath:
        return self.__dot_path
    
    def is_dotted_path(self, file_or_dotted_path:str):
        if not file_or_dotted_path:
            return False

        if self.__dot_path:
            if file_or_dotted_path.endswith(self.__dot_path.file_suffix):
                return False
        
        if file_or_dotted_path.find('/') >= 0:
            return False
        
        if os.sep != '/':
            if file_or_dotted_path.find(os.sep) >= 0:
                return False
        
        return True
    
    def join_file_or_dotted_path(self, file_or_dotted_path:str) -> 'PathContext':
        if not file_or_dotted_path:
            return file_or_dotted_path
        
        is_dotted_path = self.is_dotted_path(file_or_dotted_path)
        
        if is_dotted_path:
            return self.join_dotted_path(file_or_dotted_path)
        else:
            return self.join_file_path(file_or_dotted_path)
    
    def join_file_path(self, file_path):
        if not file_path:
            return None
        
        file_path = path_resolve(file_path, context_file = self.file_path)

        return PathContext(
            file_path=file_path
        )
        
    def join_dotted_path(self, dotted_path):
        if (not dotted_path) or self.dot_path is None:
            return None
        
        dot_path = self.dot_path.join_path(dotted_path)

        return PathContext(
            dot_path=dot_path
        )
    
    def resolve_dotted_path(self, dotted_path):
        if self.dot_path:
            return self.dot_path.resolve_dotted_path(dotted_path)
        else:
            return dotted_path