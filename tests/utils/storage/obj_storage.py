'''
python -m tests.utils.storage.obj_storage env_get
python -m tests.utils.storage.obj_storage local
python -m tests.utils.storage.obj_storage minio --saved_path './logs/aida_public/test_file'
'''
import json
from smart.utils.storage.obj_factory import *
from tests.configs import smart_env
from tests.utils import logger

def test_env_get(key=['app', 'obj_storage']):
    value = smart_env.get(key)
    logger.info('env %s: %s', key, value)


def test_local():
    factory = ObjStorageFactory(
        env=smart_env
    )
    local_storage = factory.get_store_by_env('local_model')
    local_file_path = local_storage.fget('gpt2/config.json')
    logger.info('local_file_path: %s', local_file_path)
    logger.info('local_storage._last_fget_result: %s', local_storage._last_fget_result)

    cached_storage = factory.get_store_by_env('cached_model')
    local_file_path2 = cached_storage.fget('gpt2/config.json')
    logger.info('local_file_path2: %s', local_file_path2)
    logger.info('cached_storage._last_fget_result: %s', cached_storage._last_fget_result)


def test_minio(obj_path:str=None, saved_path=None):
    obj_path = obj_path or 'sample/test.txt'
    logger.info('obj_path: %s, saved_path=%s', obj_path, saved_path)
    factory = ObjStorageFactory(env=smart_env)
    storage = factory.get_store_by_env('aida_public')
    logger.info('cache_dir: %s', storage._cache_dir)
    local_file_path = storage.fget(obj_path, local_file_path=saved_path)
    logger.info('local_file_path: %s', local_file_path)
    logger.info('storage._last_fget_result: %s', storage._last_fget_result)


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)