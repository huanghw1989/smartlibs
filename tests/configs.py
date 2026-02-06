from smart.utils.config import SmartEnv

smart_env = SmartEnv(config_dir='./tests')


def app_env(key_path, defaultVal=None):
    if isinstance(key_path, (list, tuple)):
        _path = ('app', *key_path)
    else:
        _path = ('app', key_path)
    
    return smart_env.get(_path, defaultVal)
