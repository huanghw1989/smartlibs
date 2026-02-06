import sys, logging
from smart.aaas.config import smart_env
from smart.utils.path import path_join


def all_logger(only_root=False):
    yield None, logging.getLogger()
    if not only_root:
        for name, logger in logging.root.manager.loggerDict.items():
            yield name, logger

def update_logger_stream(old_stream, new_stream, only_root=False):
    _all_logger = all_logger(only_root=only_root)
    for _name, _logger in _all_logger:
        for _handler in getattr(_logger, 'handlers', tuple()):
            if isinstance(_handler, logging.StreamHandler):
                if _handler.stream == old_stream:
                    _logger.debug("update %s stream %s -> %s", 
                        'logger-'+_name if _name else 'RootLogger', 
                        getattr(old_stream, 'name', old_stream),
                        getattr(new_stream, 'name', new_stream))
                    _handler.stream = new_stream


class TaskFileLog:
    DEFAULT_FILE_FORMAT = '{task_ns}_{task_id}.log'
    DEFAULT_AUTO_MKDIR = True

    def __init__(self, task_id, task_ns):
        self.__log_path = smart_env.get(('task_log', 'dir_path'))
        self.__fp = None
        if not self.__log_path:
            return
        self.__file_format = smart_env.get(('task_log', 'file_format'), self.DEFAULT_FILE_FORMAT)
        self.__auto_mkdir = smart_env.get(('task_log', 'auto_mkdir'), self.DEFAULT_AUTO_MKDIR)
        self.__file_name = self.__file_format.format(task_id=task_id, task_ns=task_ns)
        self.__file_path = path_join(self.__log_path, self.__file_name, auto_mkdir=self.__auto_mkdir)
        self.__fp = open(self.__file_path, mode='w', encoding='utf8')
        self.__clean_fp = None
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        sys.stdout = self.__fp
        sys.stderr = self.__fp
        update_logger_stream(self._old_stdout, self.__fp, only_root=False)
    
    def task_info(self):
        if self.__log_path:
            return {
                'file_path': self.__file_path
            }

    def close(self, reset_logger=True):
        if self.__fp:
            sys.stdout = self._old_stdout
            sys.stderr = self._old_stderr
            if reset_logger:
                update_logger_stream(self.__fp, self._old_stdout, only_root=False)
                self.__fp.close()
            else:
                self.__clean_fp = self.__fp
            self.__fp = None
    
    def clean(self):
        if self.__clean_fp:
            self.__clean_fp.close()