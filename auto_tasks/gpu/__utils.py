import logging

from smart.auto import AutoLoad

logger = logging.getLogger('auto_tasks')
auto_load = AutoLoad()

task_hook = auto_load.hook