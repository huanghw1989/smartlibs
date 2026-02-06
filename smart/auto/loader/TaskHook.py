from smart.utils import list_safe_iter

from smart.auto.loader.meta import MethodMeta
from smart.auto.loader.manage import AutoLoadManage

from smart.auto.__logger import logger_loader as logger


class TaskHook:
    def __hook_fn(self, hook_type, config=None):
        """自动载入hook方法到 auto.yml 配置, 在BaseTask子类的方法添加本装饰器
        
        Keyword Arguments:
            config {typing.Union[list, str]} -- 绑定配置 (default: {[]})
        """
        def decorator(func:callable):
            meta = MethodMeta.create(func)
            meta.func_config = list(filter(None, list_safe_iter(config)))
            meta.hook_type = hook_type
            AutoLoadManage.all_method.append(meta)

            logger.debug('TaskHook %s %s %s', hook_type, meta.cls_path, func)

            return func

        return decorator
    
    def before_task(self, config=[]):
        return self.__hook_fn('before_task', config=config)

    def after_task(self, config=[]):
        return self.__hook_fn('after_task', config=config)