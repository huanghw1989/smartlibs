import os

enable_debug = os.environ.get('REMOTE_DEBUG')

if not enable_debug:
    import re, sys
    debug = sum(1 for x in sys.argv if re.compile('^-{0,3}debug=', re.I).match(x))

if enable_debug:
    from smart.utils.remote_debug import enable_remote_debug
    enable_remote_debug()

from smart.utils.log import auto_load_logging_config, set_default_logging_config

auto_load_logging_config() or set_default_logging_config()