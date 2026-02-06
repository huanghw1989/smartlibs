import sys

from smart.utils.log import auto_load_logging_config, set_default_logging_config

is_windows = (sys.platform in ('win32',))


def on_win_process_init():
    if not is_windows:
        return
        
    auto_load_logging_config() or set_default_logging_config()
