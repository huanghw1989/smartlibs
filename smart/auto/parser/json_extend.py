from json import JSONEncoder
import pprint, inspect

from smart.utils.loader import get_import_path

from .hook import AutoYmlHookManager
from ..loader.AutoLoader import AutoLoader
from ..base import BaseTask
from ..tree import TreeFuncTask


class AutoObjJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AutoYmlHookManager):
            return [pprint.pformat(hook, indent=2) for hook in obj.hooks]

        if isinstance(obj, AutoLoader):
            return {
                'class': 'auto.loader.AutoLoader.AutoLoader',
                'module_pathes': obj.module_pathes
            }

        if isinstance(obj, TreeFuncTask):
            return get_import_path(obj.run_func)
        elif inspect.isclass(obj) or inspect.isfunction(obj):
            return get_import_path(obj)
            
        return JSONEncoder.default(self, obj)