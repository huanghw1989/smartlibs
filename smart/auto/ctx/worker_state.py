import threading


class WorkerState:
    def __init__(self) -> None:
        """Worker状态
        task_run_count: 任务运行次数
        task_error_count: 任务出错次数
        error_count: Worker出错次数
        """
        self._state = None
        self.keys = ['worker_idx', 'task_run_count', 'task_error_count', 'error_count']
    
    @property
    def worker_idx(self):
        return getattr(self._state, 'worker_idx', None)
    
    def get(self, key, default_val=None):
        return getattr(self._state, key, default_val)
    
    def incr(self, key, default_val=0):
        """递增数据

        Args:
            key (str): attr name
            default_val (int, optional): 初始化的值. Defaults to 0.

        Returns:
            int: 递增后的值
        """
        val = self.get(key, default_val=default_val) + 1
        self.set(key, val)
        return val
    
    def set(self, key, val):
        if self._state is None:
            self._state = threading.local()
        setattr(self._state, key, val)
        if key not in self.keys:
            self.keys.append(key)
    
    def update(self, **kwargs):
        if self._state is None:
            self._state = threading.local()
        state = self._state
        for key, val in kwargs.items():
            setattr(state, key, val)
            if key not in self.keys:
                self.keys.append(key)
    
    def to_dict(self):
        return {
            k:self.get(k)
            for k in self.keys
        }

    def __getstate__(self):
        """make pickable
        """
        _dict = self.__dict__.copy()
        _dict.update(
            _state=None,
        )
        return _dict