"""
python3 -m tests.utils.run_util_template test_template_str_eval
python3 -m tests.utils.run_util_template test_dict_parse
"""
import os, time
import pprint
from smart.utils import AppEnv
from smart.utils.dict import dict_find
from smart.utils.template import *
from tests.utils import logger


def test_template_str_eval(template=None):
    os.environ['TEST_FUC'] = 'test_template_str_eval'
    ns_mapping = {
        'config': {
            'func': 'test_template_str_eval',
            'script': 'run_util_template',
            'foo': {
                'bar': 1,
                'ts': time.time()
            }
        }
    }
    if template is None:
        template = """~/Work
    1 $TEST_FUC
    2 ${TEST_FUC}
    3 ${config:script}
    4 ${config:foo.ts}
    5 ${config:no_hit_key:=default_val}
    6 ${config:.ts:=null}
    7 ${config:..func:=empty}
    8 ${.bar:=None}
    9 ${no_hit_env:=default}/${config:func}
        """
    result = template_str_eval(
        template, 
        mapping=AppEnv, 
        ns_mapping=ns_mapping,
        expanduser=True,
        ns_context_path={
            'config': 'foo'
        },
        default_ns_fn=lambda var:('config' if (var or '').startswith('.') else None)
    )
    logger.info('template: %s', template)
    logger.info('result: %s', result)


def test_dict_parse():
    value = {
        'key1': 'value',
        '__pattern_x': 1,
        '__pattern_file': 'process_${pid}.log',
        'obj': {
            '__pattern_pid': '${pid}',
            '__pattern_home_path': '~/'
        }
    }

    pid = os.getpid()

    parser = DictTemplateParser(value)

    new_value = parser.parse_pattern_key(extra_envs={
        'pid': pid
    }, parse_deep=2).get_value()

    logger.info('new_value: %s', pprint.pformat(new_value))

    assert '__pattern_x' in new_value # 非str类型保持原样
    assert 'file' in new_value
    assert dict_find(new_value, ('obj', 'pid')) == str(pid)

    

if __name__ == "__main__":
    import fire
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })