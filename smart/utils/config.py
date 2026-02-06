import os

from .__logger import logger_utils
from .yaml import yaml_load_file
from .list import list_safe_iter


def search_config_file(file_name, base_dir=None):
    if not base_dir:
        base_dir = os.getcwd()

    while True:
        file_path = os.path.join(base_dir, file_name)

        if os.path.exists(file_path):
            return file_path
        
        parent_dir = os.path.dirname(base_dir)

        if not parent_dir or parent_dir == base_dir:
            break

        base_dir = parent_dir
    
    return None


class SmartEnv:
    ENV_FILE_NAME = 'smart_env.yml'

    def __init__(self, file_name=None, root_key=None, config_dir:str=None):
        file_name = file_name or self.ENV_FILE_NAME
        self._env_file = file_path = search_config_file(file_name, base_dir=config_dir)
        self._root_key = root_key or tuple()
        logger_utils.debug("SmartEnv file=%s, root_key=%s", file_path, root_key)

        if file_path:
            config_dict = yaml_load_file(file_path)
            if root_key:
                for _key in list_safe_iter(root_key):
                    if _key in config_dict:
                        config_dict = config_dict[_key]
                    else:
                        config_dict = {}
                        break
        else:
            config_dict = {}
        self.__config_dict = config_dict
    
    def __iter_key(self, key_path):
        if isinstance(key_path, (str, int)):
            yield key_path
        else:
            for key in key_path:
                yield key
    
    def get(self, key_path, default_val=None):
        obj = self.__config_dict

        for key in self.__iter_key(key_path):
            if hasattr(obj, '__getitem__') and key in obj:
                obj = obj[key]
            else:
                return default_val
        
        return obj
    
    def set(self, key_path, value):
        obj = self.__config_dict
        prev_key = None

        for key in self.__iter_key(key_path):
            if prev_key:
                if hasattr(obj, '__setitem__') and prev_key not in obj:
                    obj[prev_key] = {}
                obj = obj[prev_key]
            prev_key = key
        
        if prev_key is not None:
            obj[prev_key] = value