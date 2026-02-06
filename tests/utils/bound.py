import time

from smart.utils.bound import *


class Foo:
    # @once_fn
    @once_fn_builder(x=1, y=2)
    def bar(self, name, **kwargs):
        print('Foo.bar', self, name, kwargs)
        return (name, kwargs, time.time())


def test_once_fn():
    foo = Foo()
    print('foo.bar(abc):', foo.bar('abc'))
    print('foo.bar(def):', foo.bar('def'))


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)