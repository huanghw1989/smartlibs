import pprint, json

from smart.utils import AppEnv
from smart.utils.yaml import yaml_dumps
from smart.utils.dict import dict_safe_get
from smart.auto.parser import cmd_args
from smart.auto.parser.auto_yml import *


DEFAULT_MODULE = 'tests.auto.parser.test_auto_parser'


def __test_parse(module, format=None, node=None):
    AppEnv.set('WORK_PATH', '/home/app')
    AppEnv.set('MODEL_DIR', 'dataset/bert/chinese_L-12_H-768_A-12')

    parser = create_auto_yml_parser_by_module_path(module)
    auto_obj = parser.auto_obj

    if node:
        if isinstance(node, str):
            node = node.split('.')
        auto_obj = dict_safe_get(auto_obj, node)

    print('auto_obj:')

    if format in ('yml', 'yaml'):
        print(yaml_dumps(auto_obj))
    elif format in ('json'):
        print(json.dumps(auto_obj, ensure_ascii=False, indent=2))
    else:
        pprint.pprint(auto_obj)


def test_all(module=None, format='yml', node=None, **kwargs):
    module = module or DEFAULT_MODULE
    cmd_args.set_env_from_args(kwargs)
    __test_parse(module, format=format, node=node)


def test_if(env_val='val_case1', module=None):
    module = module or DEFAULT_MODULE

    AppEnv.set('TEST_IF_ENV', env_val)

    __test_parse(module)
    

if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)