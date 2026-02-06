
class BaseContext():
    """上下文基类
    """
    def __init__(self, configs={}):
        self.configs = configs

    def get_cfg(self, names:str, default_val=None):
        """获取配置
        
        Arguments:
            names {str|list} -- 配置名
        
        Keyword Arguments:
            default_val {any} -- 缺省值 (default: {None})
        
        Returns:
            any -- 配置值
        """
        if isinstance(names, list):
            configs = self.configs

            for key in names:
                if key in configs:
                    configs = configs[key]
                else:
                    return default_val

            return configs
        else:
            return self.configs.get(names, default_val)


class BasePip():
    """管道基类
    """
    def send(self, data, **kwargs):
        """向管道发送数据
        
        Arguments:
            data {any} -- 数据
        """
        pass
    
    def recv(self, **kwargs):
        """从管道接收数据
        
        Yields:
            any -- 接收到的数据
        """
        yield from []

    def clean(self, **kwargs):
        """清空管道数据
        """
        pass


class BaseTask():
    """任务基类
    """
    def __init__(self, pip_out:BasePip=None, pip_in:BasePip=None, context:BaseContext=None):
        self._pip_in = pip_in or BasePip()
        self._pip_out = pip_out or BasePip()
        self._context = context
    
    @property
    def pip_in(self):
        return self._pip_in
    
    @property
    def pip_out(self):
        return self._pip_out
    
    @pip_in.setter
    def pip_in(self, val):
        self._pip_in = val
    
    @pip_out.setter
    def pip_out(self, val):
        self._pip_out = val

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, val):
        self._context = val
        
    def send_data(self, data, *args, **kwargs):
        """向输出管道发送数据
        
        Arguments:
            data {any} -- 需要向输出管道发送的数据
        """
        self.pip_out and self.pip_out.send(data, *args, **kwargs)      

    def recv_data(self, *args, **kwargs):
        """从输入管道接收数据
        
        Yields:
            any -- 从输入管道接收的数据
        """
        if self.pip_in:
            for data in self.pip_in.recv(*args, **kwargs):
                yield data

    def start(self, *args, **kwargs):
        """缺省执行函数, 可不实现
        """
        pass


class BaseHook:
    def __call__(self, type, **kwargs):
        func = getattr(self, type)
        if callable(func):
            func(**kwargs)
