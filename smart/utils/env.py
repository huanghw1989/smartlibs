import os
from string import Template


def env_eval_str(template: str, extra_envs={}, expanduser=True, silence=False):
    """解析字符串中的环境变量
    例如: '${HOME}/data' => os.environ.get('HOME') + '/data'
    特殊字符说明:
    $$为转义符号, 它会被替换为单个的$
    
    Arguments:
        template {str} -- 模版字符串
        extra_envs {dict} -- 额外环境变量
        expanduser {bool} -- Expand paths beginning with '~' or '~user' (default: {True})
        silence {bool} -- 当占位符未在环境变量里，是否触发KeyError
    """
    if not template or not isinstance(template, str): 
        return template

    if expanduser and template.startswith('~'):
        template = os.path.expanduser(template)

    t = Template(template)
    substitute = t.safe_substitute if silence else t.substitute

    return substitute(os.environ, **AppEnv.all(False), **extra_envs)


class __AppEnv:
    def __init__(self):
        self.__env_dict = {}

    def set(self, key, val):
        self.__env_dict[key] = val
    
    def update(self, *args, **kwargs):
        for arg in args:
            self.__env_dict.update(arg)

        self.__env_dict.update(**kwargs)
    
    def get(self, key, defaultVal=None, include_sys=True):
        if key in self.__env_dict:

            val = self.__env_dict[key]
        elif include_sys:

            val = os.environ.get(key)
        else: 

            val = None

        return val if val is not None else defaultVal
    
    def all(self, include_sys=True):
        return {**os.environ, **AppEnv.__env_dict} if include_sys else self.__env_dict
    
    def clean(self):
        self.__env_dict = {}
    
    def __getitem__(self, key):
        return self.__env_dict[key] if key in self.__env_dict else os.environ[key]
    
    def __setitem__(self, key, val):
        self.__env_dict[key] = val
    
    def __contains__(self, key):
        return key in self.__env_dict or key in os.environ


AppEnv = __AppEnv()


def auto_set_env_by_prefix(key:str, value):
    """自动根据key前缀设置环境变量
    当key以app.开头时, 设置环境变量到AppEnv, 否则缺省设置环境变量到os

    Args:
        key (str): 环境变量名
        value (Any): 环境变量值
    """
    if key:
        if key[:4] == "app.":
            AppEnv.set(key[4:], value)
        else:
            os.environ[key] = str(value)