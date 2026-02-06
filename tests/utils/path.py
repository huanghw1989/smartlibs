'''
python -m tests.utils.path url_path_join
'''
from smart.utils.path import *
from . import logger


def test_url_path_join():
    data = [
        (['', ''], ''),
        ([], ''),
        (['1/2'], '1/2'),
        (['1/2', '3'], '1/2/3'),
        (['1/2/', '3'], '1/2/3'),
        (['1/2', '/3'], '1/2/3'),
        (['1/2/', '/3'], '1/2/3'),
        (['1/2/', '3', '4'], '1/2/3/4'),
        (['1/2/', '3/', '/4', '5'], '1/2/3/4/5')
    ]
    for path_list, expected in data:
        result = url_path_join(*path_list)
        assert result == expected, 'url_path_join({}) error, expected: {}, got: {}'.format(
            str(path_list), str(expected), str(result)
        )
    logger.info('all passed')


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)