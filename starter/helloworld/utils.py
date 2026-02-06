import logging

from smart.auto import AutoLoad

logger = logging.getLogger('example')

auto_load = AutoLoad()
task_hook = auto_load.hook


class LazyLib:
    """这里放加载耗时的module
    """
    @property
    def tf(self):
        import tensorflow as tf
        return tf
        

lazy = LazyLib()