import logging
from smart.auto import AutoLoad, TreeMultiTask

logger = logging.getLogger('test')

auto_load = AutoLoad()
auto_load.set_pkg_namespace(__package__, 'test')