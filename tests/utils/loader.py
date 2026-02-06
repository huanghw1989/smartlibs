import importlib
from smart.utils.loader import *
from smart.utils import dyn_import


class Foo:
    name = 'foo'
    
    class Bar:
        name = 'bar'


def test_find_module_file_path(path=None):
    # path = path or 'auto_tasks.tasks'
    path = path or 'tests.utils._pkg.test_yml.a.b'

    file_path = ModulePathUtil.find_module_file_path_by_dot_path(path)

    print('ori path:', path)
    print('converted path:', file_path)


def test_get_module_file_path():
    modules = [
        'smart',
        'smart.utils',
        'smart.utils.loader',
    ]
    for module_path in modules:
        module_obj = importlib.import_module(module_path)
        module_file_path = ModulePathUtil.get_module_file_path(module_obj)
        print('\n'.join([
            'path: {}'.format(module_path),
            'module_obj: {}'.format(module_obj),
            'module_file_path: {}'.format(module_file_path),
            '__package__: {}'.format(getattr(module_obj, '__package__')),
            '__name__: {}'.format(getattr(module_obj, '__name__')),
            '__file__: {}'.format(getattr(module_obj, '__file__')),
        ])+"\n\n")


def test_obj_module_dot_path():
    pathes = [
        'smart',
        'smart.utils',
        'smart.utils.loader',
        'tests.utils.loader.Foo',
        'tests.utils.loader.Foo.Bar',
    ]
    for obj_path in pathes:
        obj = dyn_import(obj_path)
        module_dot_path = ModulePathUtil.obj_module_dot_path(obj)
        print('\n'.join([
            'path: {}'.format(obj_path),
            'obj: {}'.format(obj),
            'module_dot_path: {}'.format(module_dot_path),
            # '__package__: {}'.format(getattr(module_obj, '__package__')),
            # '__name__: {}'.format(getattr(module_obj, '__name__')),
            # '__file__: {}'.format(getattr(module_obj, '__file__')),
        ])+"\n\n")


if __name__ == "__main__":
    import fire
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })