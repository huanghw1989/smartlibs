"""
python3 -m tests.utils.run_util_func test_func_safe_call
"""
from smart.utils import func_safe_call


def bar(i:int, s:str, k_i:int=None, k_s:str=None):
    print('call bar')
    args = (
        (i, 'i'),
        (s, 's'),
        (k_i, 'k_i'),
        (k_s, 'k_s')
    )
    for arg, name in args:
        print(name+':', arg, type(arg))


class Foo:
    def bar(self, i:int, s:str, k_i:int=None, k_s:str=None):
        print('call Foo.bar', self)

        args = (
            (i, 'i'),
            (s, 's'),
            (k_i, 'k_i'),
            (k_s, 'k_s')
        )
        for arg, name in args:
            print(name+':', arg, type(arg))


def test_func_safe_call():
    params = [
        (['1e2', 111], {'k_i': '2.34', 'k_s': 2.11}),
        ([Foo.bar, Foo()], {'k_i': '2.34', 'k_s': Foo}),
        ([None, None], {}),
    ]
    test_funcs = (
        (bar,),
        (Foo().bar,),
        (Foo.bar, 'static')
    )

    for args, kwargs in params:
        print('args:', args, ', kwargs:', kwargs)
        for test_func in test_funcs:
            print('\n', test_func)
            func, *other = test_func
            func_safe_call(func, [*other, *args], kwargs)
        print('')


if __name__ == "__main__":
    import fire
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })