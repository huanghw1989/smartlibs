from smart.utils.bound import *
from smart.utils.func import *


def foo(a, b:int=2, c:bool=None):
    print('foo', (a, type(a)), (b, type(b)), (c, type(c)))


def test_func_safe_call():
    print('foo')
    func_safe_call(foo, [1, '2', 'true'])

    print('\nOnceFn(foo)')
    func_safe_call(OnceFn(foo), [1, '2', 'False'])

    print('\nonce_fn(foo)')
    func_safe_call(once_fn(foo), [1, '2'])


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)