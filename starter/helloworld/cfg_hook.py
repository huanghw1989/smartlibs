import os, logging

from smart.auto import AutoYmlHook
from smart.utils import AppEnv 

from .utils import logger


class EnvHook(AutoYmlHook):
    def before_parse(self, **kwargs):
        # print('EnvHook before_parse', kwargs)
        # 设置缺省env
        if not os.environ.get('DEBUG_HEAD'):
            AppEnv.set('DEBUG_HEAD', 12)
            logger.info('set AppEnv DEBUG_HEAD %s', 12)
        
    def after_parse(self, **kwargs):
        pass
        # print('EnvHook after_parse', kwargs)