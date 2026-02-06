import multiprocessing as mp

from smart.utils.log import auto_load_logging_config, set_default_logging_config
from smart.utils.__logger import logger_utils


def on_process_init():
    # if mp.get_start_method() == 'spawn':
    #     auto_load_logging_config() or set_default_logging_config()
    auto_load_logging_config() or set_default_logging_config()


class ProcessTask:
    def __init__(self, fn):
        self.fn = fn
        self.fn_args = []
        self.fn_kwargs = {}
        self.fn_rst = None
        self.fn_err = None
        self.before_action = None
        self.after_action = None
    
    def bind(self, *args, **kwargs):
        self.fn_args = args
        self.fn_kwargs = kwargs
        return self
    
    def before(self, action_fn):
        self.before_action = action_fn
        return self
    
    def after(self, action_fn):
        self.after_action = action_fn

    def __call__(self):
        try:

            if self.before_action is not None:
                self.before_action(self, **self.fn_kwargs)
            
            self.fn_rst = self.fn(*self.fn_args, **self.fn_kwargs)

            return self.fn_rst
        except BaseException as e:

            logger_utils.exception(e)
            self.fn_err = e
        finally:

            try:
                if self.after_action is not None:
                    self.after_action(self, **self.fn_kwargs)
            except BaseException as e:
                logger_utils.exception(e)
