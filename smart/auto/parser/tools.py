import re

from smart.auto.__logger import logger
from smart.utils import tuple_fixed_len, list_safe_iter


def base_task_key(task_exp:str):
    if not task_exp: return task_exp
    pos = len(task_exp)
    for c in ('~', '('):
        find_pos = task_exp.find(c)
        if find_pos > 0:
            pos = min(pos, find_pos)
    return task_exp[:pos]


def base_task_key_match(task_dict:dict, find_keys:list):
    base_find_keys = [
        base_task_key(find_key)
        for find_key in find_keys
    ]
    for task_key, task_opts in task_dict.items():
        base_key = base_task_key(task_key)
        for i, base_find_key in enumerate(base_find_keys):
            if base_key == base_find_key:
                yield find_keys[i], task_key, task_opts


class MethodArgsParser:
    def split(self, method_exp):
        curr_pos = 0
        in_arg = False
        func, arg = '', ''
        for i, c in enumerate(method_exp):
            if not in_arg:
                if c == '(':
                    in_arg = True
                elif c == ',':
                    if func:
                        yield func, arg
                        func, arg = '', ''
                else:
                    func += c
            else:
                if c == ')':
                    in_arg = False
                else:
                    arg += c
        if not in_arg and func:
            yield func, arg

    def parse(self, method_exp, only_first=False):
        method_obj = {}
        for func, arg in self.split(method_exp):
            func, arg = func.strip(), arg.strip()
            if not func: continue
            bind_config, *_ = arg.split(',', 1)
            bind_config = list(filter(None, [
                s.strip()
                for s in bind_config.split('+')
            ]))
            opts = {}
            if bind_config:
                opts['bind_config'] = bind_config
            method_obj[func] = opts
        return method_obj


def parse_task_exp(task_exp):
    """解析任务表达式

    任务表达式格式: task_name.method(dotted_config_pathes)~join_method(dotted_config_pathes),parallel_join_method(dotted_config_pathes)~next_join_method~...

    dotted_config_pathes格式: dotted_config_path_1+dotted_config_path_2+...dotted_config_path_n

    Example: example_task.range(range.start_5 + range.step_2)~attach(sum__group3),st~log
    Example-Return:
    tuple(['example_task.range', {
        'bind_config': ['range.start_5', 'range.step_2']
        'join': [
            {
                'attach':{
                    'bind_config': ['sum__group3']
                }, 
                'st':{}
            },
            {
                'log': {}
            }
        ]
    }])

    Arguments:
        task_exp {str} -- 任务表达式
    
    Returns:
        tuple -- task_key, task_opts
    """
    main_key, *join_exp_list = task_exp.split('~')
    margs_parser = MethodArgsParser()
    main_method_obj = margs_parser.parse(main_key)

    task_key = list(main_method_obj.keys()).pop(0)
    if not task_key: return (None, None)
    task_obj = main_method_obj[task_key]

    for join_exp in join_exp_list:
        join_list = task_obj.get('join')
        if join_list is None: join_list = task_obj['join'] = []
        join_method_obj = margs_parser.parse(join_exp)
        join_list.append(join_method_obj)
    return task_key, task_obj


def is_private_key(key:str):
    if not isinstance(key, str): return False
    return key.startswith('__') and key.endswith('__')


def resolve_key_path(key_path:str, context_path:list=[]) -> list:
    """计算相对路径

    Use Example:
    resolve_key_path('.', ['a', 'b', 'c']) -> ['a', 'b', 'c']
    resolve_key_path('..', ['a', 'b', 'c']) -> ['a', 'b']
    resolve_key_path('..d', ['a', 'b', 'c']) -> ['a', 'b', 'd']
    resolve_key_path('...', ['a', 'b', 'c']) -> ['a']
    resolve_key_path('d.e', ['a', 'b', 'c']) -> ['d', 'e']
    
    Arguments:
        key_path {str} -- dotted_key_path
    
    Keyword Arguments:
        context_path {list} -- 上下文路径 (default: {None})
    
    Returns:
        list -- key path list
    """
    if key_path == '.':
        key_path_list = context_path
    elif key_path:
        key_path_list = []
        if context_path:
            match = re.match(r'^\.+', key_path)
            if match:
                level = len(match.group())
                if level > len(context_path) + 1:
                    # 相对路径溢出
                    return None
                key_path = key_path[level:]
                key_path_list = list(context_path[:-(level-1)] if level > 1 else context_path)
        if key_path:
            key_path_list.extend(key_path.split('.'))
    else:
        key_path_list = ['']
    return key_path_list


class TaskFinder:
    def __init__(self, task_map):
        self._load_task_map(task_map)

    def _load_task_map(self, task_map:dict):
        _task_map = self.task_map = {}
        _name_map = self.task_base_name_map = {}
        _alias_map = self.task_alias_map = {}

        if not task_map:
            return
        
        for name, task_dict in task_map.items():
            if is_private_key(name) or (not task_dict) or (not task_dict.get('class')):
                continue

            _task_map[name] = task_dict

            task_ns, task_base_name = tuple_fixed_len(name.rsplit('.', 1), 2, left_pad=True)

            if task_ns:
                if task_base_name not in _name_map:
                    _name_map[task_base_name] = []
                _name_map[task_base_name].append(name)
            
            alias_names = task_dict.get('alias')
            if alias_names:
                for alias_name in list_safe_iter(alias_names):
                    if not alias_name:
                        continue
                    _alias_map[alias_name] = name
    
    def find_task_dict(self, task_name):
        """查找任务字典

        Policy:
        1. 任务列表匹配
        2. 任务别名表匹配
        3. 任务简称匹配 (如果多个任务的简称一样, 会返回空)
        
        Arguments:
            task_name {str} -- 任务名
        
        Returns:
            tuple -- (task_dict, found_task_name)
        """
        if task_name in self.task_map:
            return self.task_map[task_name], task_name
        
        if task_name in self.task_alias_map:
            _task_name = self.task_alias_map[task_name]
            return self.task_map.get(_task_name), _task_name
        
        task_full_names = self.task_base_name_map.get(task_name)
        if task_full_names:
            if len(task_full_names) > 1:

                logger.warning('task %s is ambiguous, need specify one of %s', task_name, task_full_names)
            elif len(task_full_names) == 1:
                
                _task_name = task_full_names[0]
                return self.task_map.get(_task_name), _task_name
        
        return None, None
    
    def parse_task_method(self, task_key):
        task_name, func_name = tuple_fixed_len(task_key.rsplit('.', 1), 2)

        task_dict, found_task_name = self.find_task_dict(task_name)

        if (found_task_name is None) and task_key != task_name:
            task_dict, found_task_name = self.find_task_dict(task_key)
            if found_task_name:
                task_name = task_key
                func_name = None

        if found_task_name is not None:
            return task_dict, found_task_name, task_name, func_name
        else:
            return None, None, task_name, func_name


# def parse_load_exp(load_exp):
#     rst = re.split(r'\s+as\s+', load_exp)
#     return rst[0].strip(), rst[1].strip() if len(rst) > 1 else None