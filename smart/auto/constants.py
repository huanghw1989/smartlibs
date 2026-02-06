

class Constants:
    SEM_VALUE_MAX = 0
    # 缺省的Worker模式, 可选: process, thread
    DEFAULT_WORKER_MODE = 'process'
    # 缺省任务join的模式, 可选: static, object
    DEFAULT_TASK_JOIN_MODE = 'static'

    @staticmethod
    def _init():
        try:
            from _multiprocessing import SemLock
            Constants.SEM_VALUE_MAX = SemLock.SEM_VALUE_MAX
        except (ImportError):
            pass

Constants._init()