"""
python3 -m tests.auto.run_parser_tools test_method_args_parser
python3 -m tests.auto.run_parser_tools test_parse_task_exp
"""
import json

from smart.auto.parser.tools import MethodArgsParser, parse_task_exp


DEFAULT_METHOD_EXP = 'attach(sum__group3,xxx),st(a ,xx) , log'
DEFAULT_TASK_EXP = 'example_task.range(range.start_5 + range.step_2)~'+DEFAULT_METHOD_EXP+'~log'

def test_method_args_parser(method_exp=None):
    if method_exp is None: 
        method_exp = DEFAULT_METHOD_EXP

    parser = MethodArgsParser()
    print('method_exp:', method_exp)
    print('split:')
    
    for func, arg in parser.split(method_exp):
        print('\t--', (func, arg))


def test_parse_task_exp(task_exp=None):
    if task_exp is None: task_exp = DEFAULT_TASK_EXP
    print('task_exp:', task_exp)
    task_key, task_obj = parse_task_exp(task_exp)
    print('parse:', task_key, json.dumps(task_obj, indent=2))


if __name__ == "__main__":
    import fire

    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })