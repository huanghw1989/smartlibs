import typing

from smart.auto.loader.meta import MethodMeta, TaskMeta, TaskMethodsGroupMeta, ArgMethodMeta


class AutoLoadManage(object):
    all_task:typing.List[TaskMeta] = []
    all_method:typing.List[MethodMeta] = []
    all_bind_obj:typing.List[ArgMethodMeta] = []
    package_ns_map = {}

    @staticmethod
    def get_package_namespace(mod_path):
        if not mod_path:
            return None

        _ns_map = AutoLoadManage.package_ns_map
        end = len(mod_path)

        while (end > 0):
            _pkg = mod_path[0:end]

            if _pkg in _ns_map:
                _ns = _ns_map[_pkg]
                return _ns

            end = mod_path.rfind('.', 0, end)
        
        return None

    @staticmethod
    def group_task_methods():
        group_methods = {}
        group_bind_obj = {}
        
        for method_meta in AutoLoadManage.all_method:
            cls_path = method_meta.cls_path

            if not cls_path: 
                continue

            if cls_path not in group_methods:
                group_methods[cls_path] = []

            group_methods[cls_path].append(method_meta)
        
        for arg_meta in AutoLoadManage.all_bind_obj:
            arg_meta:ArgMethodMeta
            task_path = arg_meta.task_path

            if not task_path: 
                continue

            if task_path not in group_bind_obj:
                group_bind_obj[task_path] = []

            group_bind_obj[task_path].append(arg_meta)

        for task_meta in AutoLoadManage.all_task:
            pkg_ns = AutoLoadManage.get_package_namespace(task_meta.mod_path)
            
            group_meta = TaskMethodsGroupMeta(
                task_meta = task_meta,
                package_ns = pkg_ns
            )
            group_meta.task_methods = group_methods.get(group_meta.cls_path)
            group_meta.bind_objs = group_bind_obj.get(group_meta.cls_path)

            yield group_meta

