from smart.utils.dot_path import *


def test_context():
    path_pairs = [
        # context, path
        (None, None),
        (None, ''),
        (None, '.'),
        (None, 'a'),
        (None, 'a.b'),
        ('', None),
        ('', ''),
        ('', '.'),
        ('', 'a'),
        ('', 'a.b'),
        ('.', None),
        ('.', ''),
        ('.', 'a'),
        ('.', 'a.b'),
        ('.', '.'),
        ('.', '..'),
        ('a', None),
        ('a', '.'),
        ('a', 'a'),
        ('a', 'a.b'),
        ('a.b', None),
        ('a.b', '.'),
        ('a.b', 'c'),
        ('a.b', '.c.d'),
        ('a.b', '..c.d'),
        ('a.b', '...c.d'),
        ('a.b', '...'),
    ]

    for ctx, path in path_pairs:
        print('ctx=#{}#, path=#{}#'.format(ctx, path))
        print('resolved: #{}#'.format(DotPathContext(ctx_dotted_dir=ctx).resolve_dotted_path(path)))
        print('')


def test_dot_path():
    path = DotPath.create('tests.utils._pkg.test_yml.a.b', file_suffix='.py')
    dotted_path_and_expect_abs_path_list = [
        ('....__init__', 'tests.__init__'),
        ('.auto.parser.auto_yml', 'tests.auto.parser.auto_yml'),
        ('...utils.dot_path', 'tests.utils.dot_path'),
        ('._pkg.test_yml.__init__', 'tests.utils._pkg.test_yml.__init__'),
        ('tests.utils.loader', 'tests.utils.loader')
    ]

    print('file_path:', path.file_path)
    print('')

    _path = path
    for dotted_path, expect_abs_path in dotted_path_and_expect_abs_path_list:
        print('ori dotted_path:', dotted_path)
        _path = _path.join_path(dotted_path)
        
        print('abs dotted_path:', _path.dotted_path)

        if expect_abs_path is not None:
            assert expect_abs_path == _path.dotted_path
            print('assert success')

        print('file_path:', _path.file_path)
        print('')


def test_cast_dot_pattern_to_file_pattern():
    patterns = [
        '.',
        '.*',
        '..*',
        '...ab.c.*',
        'a.b.c',
        'aa',
    ]

    for pattern in patterns:
        file_pattern = cast_dot_pattern_to_file_pattern(pattern)
        print('{} -> {}'.format(pattern, file_pattern))


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)