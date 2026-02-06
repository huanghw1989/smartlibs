from smart.utils.config import *

from . import logger


def test_get_set(root_key="aaas"):
    key_value_list = [
        (('task_log', 'dir_path'), "xxx"),
        (('a', 'b'), "a.b"),
    ]
    smart_env = SmartEnv(root_key=root_key)
    for key_val in key_value_list:
        key, val = key_val
        old_val = smart_env.get(key)
        logger.info("old_value %s: %s %s", key, type(old_val), old_val)
        smart_env.set(key, val)
        new_val = smart_env.get(key)
        logger.info("new_value %s: %s %s", key, type(new_val), new_val)
        assert new_val == val


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)