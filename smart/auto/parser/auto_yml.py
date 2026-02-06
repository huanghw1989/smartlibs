"""auto配置文件读取
syntax 解析顺序: 
    template: 执行模版表达式(环境变量替换)
    if: 条件判断(by 环境变量)
    ref: 引用配置
    extend: 从配置继承
    flow: tree节点特有属性, 将自动转化为tree依赖树
    sibling: 元素拷贝到临近节点 (不覆盖原有属性, 不会拷贝到__xxx__节点)


configs节点支持syntax: template, if, extend
args节点支持syntax: ref
kwargs节点支持syntax: ref, extend
tree节点支持: flow, sibling
tree.task节点支持: template, if, extend
"""
import os, inspect, re
from collections import OrderedDict

from smart.utils import \
    dict_deep_merge, dict_safe_get, dict_get_or_set, iter_list_or_dict, \
    yaml_load_file, \
    env_eval_str, AppEnv, \
    path_resolve, path_join, \
    list_safe_iter, tuple_fixed_len, \
    template_str_eval, \
    dyn_import

from smart.utils.number import safe_parse_int
from smart.utils.cast import cast_val
from smart.utils.dag import DagItemsTool
from smart.utils.dot_path import DotPath
    
from smart.auto.base import BaseHook
from smart.auto.loader.AutoLoader import AutoLoader
from smart.auto.loader.meta import MethodMeta, TaskMethodsGroupMeta

from smart.auto.parser.path_ctx import PathContext
from smart.auto.parser.hook import AutoYmlHook, AutoYmlHookManager
from smart.auto.parser.tools import base_task_key, base_task_key_match, is_private_key, parse_task_exp, MethodArgsParser, resolve_key_path, TaskFinder

from smart.auto.__logger import logger, logger_trace


class AutoYmlParser:
    DEFAULT_KEY = '__default__'
    PLAIN_KEY = '__plain__'

    HOOK_KEY = '__hook'
    LOADER_KEY = '__loader'

    def __init__(self, auto_obj, yml_path:DotPath=None, yml_file=None):
        self.auto_obj = auto_obj
        self.hook_m:AutoYmlHookManager = AutoYmlHookManager()
        self.loader = AutoLoader()

        self.path_ctx = PathContext(file_path=yml_file, dot_path=yml_path)

        self.__imported_dict = set()

        if yml_file:
            self.__imported_dict.add(yml_file)
    
    @staticmethod
    def load_yml_file(file_path = None):
        auto_obj = yaml_load_file(file_path) or {}
        parser = AutoYmlParser(auto_obj, yml_file=file_path)

        return parser

    @staticmethod
    def load_yml_path(yml_path:DotPath):
        file_path = yml_path.file_path

        auto_obj = yaml_load_file(file_path) or {}
        parser = AutoYmlParser(auto_obj, yml_file=file_path, yml_path=yml_path)

        return parser
    
    def parse_all_syntax(self):
        """ 执行全部语法 """
        auto_obj = self.auto_obj

        self.parse_hook_node(auto_obj)
        self.hook_m.triger_once('before_parse')
        self.parse_load_node(auto_obj.get('tasks'))

        auto_obj = self.auto_obj = self.parse_import_node()

        self.parse_configs_node()
        self.parse_tasks_node(auto_obj)
        self.parse_trees_node(auto_obj)
        self.loader_load_tasks()
        self.hook_m.triger('after_parse')

        return self

    def parse_import_node(self, auto_obj=None, path_ctx=None, ctx_path:DotPath=None, deep_parse=True):
        """解析yaml配置中import节点
        """
        if path_ctx is None: 
            path_ctx = self.path_ctx

        if auto_obj is None: 
            auto_obj = self.auto_obj

        imported_dict = self.__imported_dict

        i_files = auto_obj.pop("import", [])
        configs = auto_obj.get('configs') or {}

        if i_files:
            for i_file in list_safe_iter(i_files):
                i_file = template_str_eval(i_file, mapping=AppEnv, ns_mapping={
                    'config': configs
                }, expanduser=True)

                i_file_ctx = path_ctx.join_file_or_dotted_path(i_file)

                i_file_path = i_file_ctx.file_path if i_file_ctx else i_file

                if not i_file_path or i_file_path in imported_dict:
                    continue
                
                i_auto_obj = self.import_yml_file(i_file_path, path_ctx=i_file_ctx)

                if deep_parse and isinstance(i_auto_obj, dict):
                    i_auto_obj = self.parse_import_node(auto_obj=i_auto_obj, path_ctx=i_file_ctx, deep_parse=deep_parse)

                auto_obj = dict_deep_merge(i_auto_obj, auto_obj, no_copy=True)

        return auto_obj
    
    def __on_import(self, auto_obj, path_ctx:PathContext=None):
        """ 新的yml文件加载后触发 """
        if auto_obj:
            self.parse_hook_node(auto_obj, path_ctx=path_ctx)
            self.hook_m.triger_once('before_parse')
            self.parse_load_node(auto_obj.get('tasks'), path_ctx=path_ctx)

    def import_yml_file(self, file, path_ctx:PathContext=None):
        """ 加载新的yml文件 """
        logger_trace.debug('AutoYmlParser.import_yml_file %s, ctx_dot_path=%s', 
                file, path_ctx.dot_path.dotted_path if path_ctx and path_ctx.dot_path else None)

        self.__imported_dict.add(file)
        auto_obj:dict = yaml_load_file(file)

        if not auto_obj or not isinstance(auto_obj, dict):
            return {}

        self.__on_import(auto_obj, path_ctx=path_ctx)

        return auto_obj

    def parse_load_node(self, tasks_node, path_ctx=None, load_key='__load__'):
        if tasks_node is None or load_key not in tasks_node: 
            return
        
        if path_ctx is None:
            path_ctx = self.path_ctx

        load_list = tasks_node.pop(load_key)

        for dotted_path, load_opts in iter_list_or_dict(load_list, list_as_key=True):
            if not dotted_path:
                continue

            if path_ctx.dot_path:
                resolved_dotted_path = path_ctx.dot_path.resolve_dotted_path(dotted_path)
            else:
                resolved_dotted_path = dotted_path
            
            if resolved_dotted_path.startswith('.'):
                ctx_dotted_path = path_ctx.dot_path.dotted_path if path_ctx and path_ctx.dot_path else None
                logger.warning('AutoYmlParser can not load relative path %s, ori_path=%s, ctx_path=%s', 
                        resolved_dotted_path, dotted_path, ctx_dotted_path)
                continue

            self.loader.load(resolved_dotted_path, opts=load_opts)

    def __loader_cast_method_meta(self, method_meta:MethodMeta):
        if not method_meta: 
            return {}

        return {
            'bind_config': method_meta.func_config,
            'hook_type': method_meta.hook_type
        }
    
    def _rename_module(self, ori_name, rename):
        if not rename:
            return ori_name

        if rename.endswith('.'):
            return rename + ori_name
        else:
            return rename + '.' + ori_name.rsplit('.', 1)[-1]

    def loader_load_tasks(self):
        """将loader的任务合并到auto_obj, key冲突时原数据优先
        """
        root_auto_obj = self.auto_obj
        loader:AutoLoader = self.loader
        task_node = root_auto_obj.get('tasks')

        if task_node is None: 
            task_node = root_auto_obj['tasks'] = {}

        for task_methods_meta, load_opts in loader.group_task_methods():
            task_methods_meta:TaskMethodsGroupMeta
            load_opts = load_opts or {}

            task_meta = task_methods_meta.task_meta
            task_name = task_meta.task_name
            task_alias = task_meta.task_alias

            if not task_name:
                continue

            as_module:str = load_opts.get('as_module')
            task_ns = as_module or task_methods_meta.package_ns

            # rename task
            task_name = self._rename_module(task_name, task_ns)

            # rename alias
            if task_alias:
                alias_module = load_opts.get('alias_module') or task_methods_meta.package_ns
                task_alias = [
                    self._rename_module(ori_name, alias_module)
                    for ori_name in list_safe_iter(task_alias)
                    if ori_name
                ]

            yml_task_obj = task_node.get(task_name)

            if yml_task_obj is None: 
                yml_task_obj = task_node[task_name] = {}

            cls_path = task_methods_meta.cls_path
            cls_path_yml = yml_task_obj.get('class')

            if not cls_path_yml:

                yml_task_obj['class'] = task_meta.task_cls or cls_path
            elif cls_path_yml != cls_path:
                
                raise ValueError('Task Class Conflit, loader_cls is {} and yml is {}'.format(
                    cls_path, cls_path_yml
                ))
            
            loader_task_obj = {}
            if task_alias:
                loader_task_obj['alias'] = task_alias
            
            if loader_task_obj:
                yml_task_obj = dict_deep_merge(loader_task_obj, yml_task_obj, no_copy=True)

            if task_methods_meta.task_methods:
                to_extend = {}

                for method_meta in task_methods_meta.task_methods:
                    to_extend[method_meta.func_name or 'start'] = self.__loader_cast_method_meta(method_meta)

                yml_task_obj['def'] = dict_deep_merge(to_extend, yml_task_obj.get('def'), no_copy=True)

            if task_methods_meta.bind_objs:
                to_extend = {}

                for bind_obj_meta in task_methods_meta.bind_objs:
                    func_name = bind_obj_meta.method_meta.func_name if bind_obj_meta.method_meta.cls_name else 'start'

                    if func_name not in to_extend: 
                        to_extend[func_name] = {'bind_obj': {}}

                    bind_node = to_extend[func_name]['bind_obj']
                    bind_node[bind_obj_meta.arg_name] = {
                        'path': bind_obj_meta.arg_path,
                        'config': bind_obj_meta.arg_config
                    }

                yml_task_obj['def'] = dict_deep_merge(to_extend, yml_task_obj.get('def'), no_copy=True)

            task_node[task_name] = yml_task_obj
                    
    def parse_syntax_extend(self, node, configs, extend_key='__extend__', deep_parse=False, before_merge=None, context_path=None):
        """ 解析 __extend__ 语法
        限定: dict节点
        值: list[dotted_config_path]
        作用: 继承配置节点的值, 支持多重继承
        """
        if node is None: 
            return

        if self.PLAIN_KEY in node:
            del node[self.PLAIN_KEY]
            return

        to_extends = node.pop(extend_key, [])
        
        if deep_parse:
            # deep parse extend(until has __plain__ key)
            for sub_key, sub_node in node.items():
                if isinstance(sub_node, dict):
                    # if extend_key in sub_node: print('deep parse:', sub_node)
                    self.parse_syntax_extend(sub_node, configs, extend_key=extend_key, deep_parse=deep_parse)

        for to_extend_key in list_safe_iter(to_extends):
            to_extend_key = tuple(to_extend_key if isinstance(to_extend_key, list) else resolve_key_path(to_extend_key, context_path=context_path))
            to_extend_dict = dict_safe_get(configs, to_extend_key)

            if isinstance(to_extend_dict, dict):
                if before_merge:
                    before_merge(to_extend_key, to_extend_dict)

                # if extend_key in to_extend_dict:
                #     # 继承的config节点可能未执行extend, 需deep_parse
                #     self.parse_syntax_extend(to_extend_dict, configs, extend_key=extend_key, deep_parse=True)

                for p_key, p_val in to_extend_dict.items():
                    if p_key not in node:
                        node[p_key] = p_val

    def parse_syntax_ref(self, parent_node, node_keys, configs, ref_key='__ref__'):
        """ 解析 __ref__ 语法 
        值: dotted_config_path or list[config_key]
        作用: 引用配置节点, 一般用于list节点
        """
        if parent_node is None: 
            return

        for key in node_keys:
            if key not in parent_node:
                continue

            node = parent_node[key]

            if not node or ref_key not in node:
                continue

            to_ref = node.get(ref_key)

            del node[ref_key]

            if isinstance(to_ref, str):
                to_ref = to_ref.split('.')

            parent_node[key] = dict_safe_get(configs, to_ref)

    def parse_syntax_if(self, node, if_key='__if__'):
        """ 解析 __if__ 语法 
        限定: 仅支持configs节点
        作用: 根据环境变量选择子节点
        语法: 
        __if__:
          ENV_NAME | cast_fn(ENV_NAME):
            VAL1: [dict]
            VAL2: [dict]
            __default__: [dict]
        """
        if node is None: 
            return

        if_dict = node.pop(if_key, {})

        for env_exp, opts in if_dict.items():
            _match = re.match(r"^\s*(\w+)\(\s*(\w+)\s*\)\s*$", env_exp)
            if _match:
                cast_type = _match.group(1)
                cast_fn = lambda val: cast_val(cast_type, val) if not is_private_key(val) else val
                env_key = _match.group(2)
            else:
                cast_fn = str
                env_key = env_exp.strip()

            opt_key = cast_fn(AppEnv.get(env_key))

            opts = {
                cast_fn(k): v
                for k, v in (opts or {}).items()
            }

            opt_dict = opts.get(opt_key) if opt_key is not None and opt_key in opts else opts.get(self.DEFAULT_KEY)

            if opt_dict:
                node.update(
                    dict_deep_merge(node, opt_dict, no_copy=True)
                )
    
    def __default_ns_fn(self, key_path):
        """相对路径的key_path, 缺省config命名空间
        """
        if key_path and key_path.startswith('.'):
            return 'config'
        else:
            return None

    def parse_syntax_template(self, node, configs, context_path=None, template_key='__template__'):
        """ 解析 __template__ 语法 
        值类型: dict[key:str_template]
        作用: 根据环境变量或配置节点替换字符串模版
        字符串模版: $ENV_NAME, ${ENV_NAME}, ${config:dotted_config_path}
        """
        if node is None: 
            return

        template_dict = node.pop(template_key, {})
        ns_context_path = {'config': context_path} if context_path else None

        for key, templ in template_dict.items():
            val = template_str_eval(
                templ, 
                mapping=AppEnv, 
                ns_mapping={
                    'config': configs
                }, 
                expanduser=True, 
                ns_context_path=ns_context_path,
                default_ns_fn=self.__default_ns_fn)
            node[key] = val

    def parse_syntax_flow(self, node, flow_key='__flow__', dependance_key = '__dependance__'):
        """ 解析 __flow__ 语法 
        限定: 仅树节点(trees节点的子节点)下可用
        值类型: list[task_expression]
        作用: 
            按照值顺序设置任务先后依赖关系
            同时会解析任务表达式, 并将解析后的run_opts合并的树节点对应任务下, 合并时冲突保留原值
        """
        if node is None: 
            return

        flow_list = node.pop(flow_key, [])
        dependance_list = node.get(dependance_key, None)

        if dependance_list is None: 
            dependance_list = node[dependance_key] = []

        for i, task_exp in enumerate(flow_list):
            flow_list[i] = parse_task_exp(task_exp)

        for i in range(1, len(flow_list)):
            prev, next = flow_list[i-1], flow_list[i]
            dependance_list.append((prev[0], next[0]))

        for i in range(0, len(flow_list)):
            task_key, task_opts = flow_list[i]

            # if not task_opts: 
            #     continue

            flow_task_key, flow_task_opts = self.normalize_tree_task(task_key, task_opts)

            node[flow_task_key] = dict_deep_merge(
                flow_task_opts,
                node.get(flow_task_key, None)
            )

    def parse_syntax_sibling(self, node, sibling_key='__sibling__'):
        """ 解析 __sibling__ 语法 
        作用: 将__sibling__节点下的所有元素拷贝到兄弟节点, key冲突时保留原值(即使原值为None也不覆盖)
        """
        if node is None: 
            return

        sibling_node = node.pop(sibling_key, None)

        if sibling_node:
            for extend_key, extend_val in sibling_node.items():
                for node_key, node_dict in node.items():
                    if is_private_key(node_key): 
                        continue

                    if node_dict is None: 
                        node[node_key] = node_dict = {}

                    if extend_key not in node_dict:
                        node_dict[extend_key] = extend_val

    def parse_configs_node(self):
        auto_obj = self.auto_obj
        configs = auto_obj.get('configs')
        if not configs: return
        parsed_key = set()

        def __before_extend_merge(extend_key, extend_dict):
            if extend_key not in parsed_key:
                __deep_parse(extend_dict, extend_key)

        def __deep_parse(node, key_path:tuple):
            if not isinstance(node, dict): return
            # deep parse extend(until has __plain__ key)

            if self.PLAIN_KEY in node:
                del node[self.PLAIN_KEY]
                return

            self.parse_syntax_template(node, configs, context_path=key_path)
            self.parse_syntax_if(node)

            # if语法可能新增__template__节点, 重复解析一遍template
            self.parse_syntax_template(node, configs, context_path=key_path)

            self.parse_syntax_extend(node, configs, before_merge=__before_extend_merge, context_path=key_path)
            parsed_key.add(key_path)

            for sub_key, sub_node in node.items():
                if isinstance(sub_node, dict):
                    __deep_parse(sub_node, (*key_path, sub_key))

        __deep_parse(configs, tuple())

    def parse_hook_node(self, auto_obj, path_ctx=None):
        if 'hooks' in auto_obj:
            hook_pathes = auto_obj.pop('hooks')
            path_ctx = path_ctx or self.path_ctx

            for hook_path in list_safe_iter(hook_pathes):
                hook_path = path_ctx.resolve_dotted_path(hook_path)
                hook_val = dyn_import(hook_path)
                hook_obj = None

                if inspect.isclass(hook_val) and issubclass(hook_val, BaseHook):
                    hook_obj = hook_val(run_obj=auto_obj)
                elif callable(hook_val):
                    hook_obj = hook_val
                if hook_obj:
                    self.hook_m.add_hook(hook_obj)

    def parse_args_node(self, node, configs):
        if node is None: 
            return

        self.parse_syntax_ref(node, ['args', 'kwargs'], configs)

        if 'kwargs' in node:
            kwargs_node = node['kwargs']
            self.parse_syntax_template(kwargs_node, configs)
            self.parse_syntax_extend(kwargs_node, configs)
    
    def dict_flattern(self, parent_node, node_keys, flattern_end):
        if not parent_node:
            return
        
        for key in list_safe_iter(node_keys):
            node = parent_node.get(key)
            
            if not node:
                continue

            updated_node = {}

            for sub_key, sub_node in node.items():
                if isinstance(sub_key, str) and len(sub_key) and sub_key[-1] in flattern_end:
                    if isinstance(sub_node, dict):
                        self.dict_flattern(node, sub_key, flattern_end)
                        sub_node = node[sub_key]

                        for k, v in sub_node.items():
                            updated_node[sub_key+k] = v
                else:
                    updated_node[sub_key] = sub_node

            parent_node[key] = updated_node

    def parse_tasks_node(self, auto_obj):
        if 'tasks' not in auto_obj:
            return
        
        self.dict_flattern(auto_obj, 'tasks', ('.',))
        tasks = auto_obj['tasks']
        configs = auto_obj.get('configs', {})

        for key, task_node in tasks.items():
            if 'init' in task_node:
                self.parse_args_node(task_node['init'], configs)

            if 'def' in task_node and task_node['def']:
                for func, node in task_node['def'].items():
                    self.parse_args_node(node, configs)

    def parse_join_node(self, join_node):
        if not join_node: 
            return None

        parser = MethodArgsParser()
        joins = []

        if isinstance(join_node, str):
            join_list = join_node.split('~')
        elif isinstance(join_node, list):
            join_list = join_node
        else:
            return None

        for join_exp in join_list:
            if isinstance(join_exp, dict):

                joins.append(join_exp)
            elif isinstance(join_exp, str):

                join_obj = parser.parse(join_exp)
                if join_obj:
                    joins.append(join_obj)
            elif isinstance(join_exp, list):

                join_obj = {}

                for sub_join_exp in join_exp:
                    sub_join_obj = parser.parse(sub_join_exp)

                    if sub_join_obj:
                        join_obj.update(sub_join_obj)

                joins.append(join_obj)

        return joins

    def normalize_tree_task(self, task_key, run_obj):
        base_key, exp_obj = parse_task_exp(task_key)

        if run_obj is None: 
            run_obj = {}
        
        for opt_name in ('worker_num', ):
            if opt_name in run_obj:
                run_obj[opt_name] = safe_parse_int(run_obj.get(opt_name))

        if 'join' in run_obj:
            run_obj['join'] = self.parse_join_node(run_obj.get('join'))

        exp_joins = exp_obj.pop('join', [])

        if exp_joins:
            run_obj['join'] = [*exp_joins, *(run_obj.get('join') or [])]

        if exp_obj:
            for k, v in exp_obj.items():
                if k not in run_obj:
                    run_obj[k] = v

        next_keys = run_obj.pop('next', None)
        prev_key = run_obj.pop('prev', None)

        if prev_key and isinstance(prev_key, str):
            run_obj['prev'] = base_task_key(prev_key)

        if next_keys:
            run_obj['next'] = [ 
                base_task_key(next_key) 
                for next_key in list_safe_iter(next_keys) 
                if next_key
            ]

        return base_key, run_obj

    def normalize_tree_node(self, tree_node, dependance_key = '__dependance__'):
        if tree_node is None: return {}
        normalized_tree = {}
        dependance = set()
        dep_list = tree_node.pop(dependance_key, None)

        if dep_list:
            for dep in dep_list:
                dependance.add(tuple(dep))

        for sub_key, sub_dict in tree_node.items():
            if is_private_key(sub_key):
                normalized_tree[sub_key] = sub_dict
                continue

            task_key, run_obj = self.normalize_tree_task(sub_key, sub_dict)
            prev_task_key = run_obj.pop('prev', None)

            if prev_task_key:
                dependance.add((prev_task_key, task_key))

            for next_task_key in list_safe_iter(run_obj.pop('next', [])):
                dependance.add((task_key, next_task_key))

            normalized_tree[task_key] = run_obj

        for prev_key, next_key in dependance:
            prev_task = normalized_tree.get(prev_key)
            next_task = normalized_tree.get(next_key)

            if prev_task is None: 
                prev_task = normalized_tree[prev_key] = {}

            if next_task is None: 
                next_task = normalized_tree[next_key] = {}

            prev_task['next'] = [
                *prev_task.get('next', []),
                next_key
            ]
            next_task['prev'] = prev_key

        return normalized_tree

    def sort_tree_node(self, node):
        if not node: 
            return {}

        dt = DagItemsTool(prev_key_name='prev', next_key_name='next')

        return dt.sort_item_dict(node, raise_err_on_cycle=True)
        
    def parse_trees_node(self, auto_obj):
        if 'trees' not in auto_obj: 
            return

        trees = auto_obj.get('trees') or {}
        configs = auto_obj.get('configs') or {}

        for tree_name, tree_node in trees.items():
            if not tree_node: 
                continue

            for sub_key, sub_val in tree_node.items():
                if isinstance(sub_val, dict):
                    self.parse_syntax_template(sub_val, configs)
                    self.parse_syntax_if(sub_val)
                    self.parse_syntax_extend(sub_val, configs, deep_parse=True)

            tree_node = self.normalize_tree_node(tree_node)
            self.parse_syntax_flow(tree_node)
            self.parse_syntax_sibling(tree_node)
            tree_node = self.normalize_tree_node(tree_node)
            tree_node = self.sort_tree_node(tree_node)
            trees[tree_name] = tree_node
    
    def __resolve_config_dict(self, config_dict):
        configs = self.auto_obj.get('configs') or {}
        self.parse_syntax_template(config_dict, configs)
        self.parse_syntax_if(config_dict)
        self.parse_syntax_extend(config_dict, configs)

        return config_dict

    def bind_arg(self, bind_arg_dict):
        if not bind_arg_dict: 
            return

        task_node = dict_get_or_set(self.auto_obj, 'tasks', default_val={})
        finder = TaskFinder(task_node)
        
        for task_key, arg_dict in bind_arg_dict.items():
            if not arg_dict or not isinstance(arg_dict, dict): 
                continue

            arg_dict = self.__resolve_config_dict(arg_dict)

            task_name, func_name = tuple_fixed_len(task_key.rsplit('.', 1), 2)
            task_dict, found_task_name, task_name, func_name = finder.parse_task_method(task_key)

            func_name = func_name or 'start'
            bind_arg_node = dict_get_or_set(
                task_node, [found_task_name or task_name, 'def', func_name, 'bind_arg'], default_val={})
            bind_arg_node.update(arg_dict)
            

def create_auto_yml_parser_by_file(file, resolve_env=True) -> AutoYmlParser:
    file = env_eval_str(file) if resolve_env else file

    parser = AutoYmlParser.load_yml_file(file)
    parser.parse_all_syntax()

    return parser


def create_auto_yml_parser_by_module_path(module_path) -> AutoYmlParser:
    if not module_path:
        return None
        
    module_path = env_eval_str(module_path)
    
    dot_path = DotPath.create(module_path, '.yml')

    parser = AutoYmlParser.load_yml_path(dot_path)
    parser.parse_all_syntax()

    return parser