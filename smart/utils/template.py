import os, re

from .dict import dict_safe_get
from .env import env_eval_str


class NamespaceTemplate:
    def __init__(self, template:str, context_path=None, ns_context_path=None, default_ns_fn=None):
        self.template = template
        self.idpattern = r'(\$([_a-zA-Z0-9]+)|\$\{([_\.a-zA-Z0-9]+\:?[_\.a-zA-Z0-9]+(\:=[^}\s]*)?)\})'
        self.match_list = list(
            re.finditer(self.idpattern, self.template)
        )
        self.context_path = context_path.split('.') if isinstance(context_path, str) else context_path
        self.ns_context_path = {
            k: v.split('.') if isinstance(v, str) else v
            for k, v in (ns_context_path or {}).items()
        }
        self.default_ns_fn = default_ns_fn
    
    def __get_mapping_val(self, mapping, key_path, context_path=None):
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

        return dict_safe_get(mapping, key_path_list)

    def substitute(self, mapping=None, ns_mapping=None, no_hit_handler=None):
        template = self.template
        piece_list = []
        prev_pos = 0
        
        for match in self.match_list:
            start, end = match.start(), match.end()
            piece_list.append(template[prev_pos:start])
            var_key = match.group(2) or match.group(3)
            var_key_info = var_key.split(':=', 1)
            ns_var = var_key_info[0].split(':', 1)
            default_val = var_key_info[1] if len(var_key_info) > 1 else None

            if len(ns_var) > 1:
                ns, var = ns_var[0], ns_var[1]
            else:
                ns, var = None, ns_var[0]
                if self.default_ns_fn:
                    ns = self.default_ns_fn(var)

            _mapping = mapping if ns is None else (ns_mapping or {}).get(ns, {})
            context_path = self.context_path if ns is None else self.ns_context_path.get(ns)
            replace = self.__get_mapping_val(_mapping or {}, var, context_path=context_path)

            if replace is None:
                if default_val is not None:

                    replace = default_val
                else:

                    if no_hit_handler:
                        replace = no_hit_handler(ns_var)
                    else:
                        raise ValueError('Template substitute mapping has no key='+var_key)

            piece_list.append(str(replace))
            prev_pos = end

        piece_list.append(template[prev_pos:])

        return ''.join(piece_list)
    
    def safe_substitute(self, mapping=None, ns_mapping=None):
        no_hit_handler = lambda ns_var: ''

        return self.substitute(mapping=mapping, ns_mapping=ns_mapping, no_hit_handler=no_hit_handler)


def template_str_eval(template:str, mapping=None, ns_mapping:dict=None, expanduser=False, 
                    context_path=None, ns_context_path=None, default_ns_fn=None):
    """执行字符串模版替代
    
    字符串模版: $mapping_key, ${mapping_key}, ${ns_name:dotted_ns_mapping_key_path}

    Arguments:
        template {str} -- 字符串模版
    
    Keyword Arguments:
        mapping {dict} -- 映射字典 (default: {None})
        ns_mapping {dict} -- 带命名空间的映射字典 (default: {None})
        expanduser {bool} -- 是否解析用户路径符'~' (default: {False})
        ns_context_path {dict} -- 命名空间相对路径的上下文目录 (default: {None})
        default_ns_fn {callable} -- 缺省命名空间获取函数, (key_path)=>namespace (default: {None})
    
    Returns:
        [type] -- [description]
    """
    if expanduser and template.startswith('~'):
        template = os.path.expanduser(template)

    ns_template = NamespaceTemplate(
        template, 
        context_path=context_path, 
        ns_context_path=ns_context_path,
        default_ns_fn=default_ns_fn)
    
    return ns_template.substitute(mapping, ns_mapping)


def find_quote_str(text, quote_start, quote_end, escape_char='\\'):
    """查找引用文本

    Example: list(find_quote_str(r'{{a\{b\}c}}d{{ef}}g', '{{', '}}'))

    Arguments:
        text {str} -- 文本
        quote_start {str} -- 引用开始字符
        quote_end {str} -- 引用结束字符

    Keyword Arguments:
        escape_char {str} -- 转义字符 (default: {'\'})

    Yields:
        tuple -- (pos_start, pos_end, substr), substr为转义后的字符串
    """
    if not text:
        yield from []

    pos_start = None
    skip = 0
    strip_mode = False
    substr = ''
    len_s, len_e = len(quote_start), len(quote_end)
    start_char, end_char = quote_start[0], quote_end[0]

    for i in range(len(text)):
        if skip:
            skip -= 1
            continue

        c = text[i]

        if c == escape_char:
            if text[i+1] in (escape_char, start_char, end_char):
                skip = 1
                if pos_start is not None:
                    substr += text[i+1]
                continue

        if pos_start is None:
            if c == start_char:
                if len_s > 1 and text[i:i+len_s] != quote_start:
                    continue

                pos_start = i
                skip = len_s - 1
        else:
            if c == end_char:
                if len_e == 1 or (text[i:i+len_e] == quote_end):
                    yield pos_start, i+len_e, substr
                    pos_start, substr = None, ''
                    skip = len_e - 1
                    continue
            substr += c


class DictTemplateParser:
    def __init__(self, value:dict) -> None:
        self._value = value or {}

    def get_value(self):
        return self._value

    def _parse_pattern_key(self, value:dict, extra_envs={}, expanduser=True, parse_deep:int=1, key_prefix='__pattern_'):
        if parse_deep == 0:
            return value
        
        extra_envs = extra_envs or {}
        to_del_keys = []
        to_update = {}
        for key, sub_value in value.items():
            if isinstance(sub_value, dict):
                if parse_deep:
                    new_value = self._parse_pattern_key(
                        value = sub_value,
                        extra_envs = extra_envs,
                        expanduser = expanduser,
                        parse_deep = parse_deep-1,
                        key_prefix = key_prefix
                    )
                continue
            if not isinstance(sub_value, str):
                continue
            if isinstance(key, str) and key.startswith(key_prefix):
                to_del_keys.append(key)
                new_key = key[len(key_prefix):]
                new_value = env_eval_str(
                    sub_value, 
                    extra_envs=extra_envs, 
                    expanduser=expanduser,
                    silence=True
                )
                to_update[new_key] = new_value
        
        for key in to_del_keys:
            del value[key]

        value.update(to_update)

        return value
    
    def parse_pattern_key(self, extra_envs={}, expanduser=True, parse_deep:int=1, key_prefix='__pattern_'):
        self._parse_pattern_key(
            self._value, 
            extra_envs=extra_envs, 
            expanduser=expanduser, 
            parse_deep=parse_deep, 
            key_prefix=key_prefix
        )
        return self