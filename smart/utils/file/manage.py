import io


class ResManage:
    def __init__(self, res_open_fn:callable=None, close_func_name='close'):
        self.opened = {}
        self.res_open_fn = res_open_fn
        self.close_func_name = close_func_name
    
    def get_res(self, name=''):

        if name not in self.opened:
            if not self.res_open_fn: raise ValueError("res_open_fn can't be None")
            self.opened[name] = self.res_open_fn(name)

        return self.opened[name]
    
    def close(self):
        for name in list(self.opened.keys()):
            res = self.opened.pop(name)
            getattr(res, self.close_func_name)()
            
    def __enter__(self):
        return self

    def __exit__(self, errClass, errMsg, errTrace):
        self.close()


class FileManage(ResManage):
    def __init__(self, file_path_fn=None, open_opts={}):
        self.open_opts = {
            'encoding': 'utf8'
        }
        self.open_opts.update(open_opts)
        self.file_path_fn = file_path_fn
        self.all_file = {}
        super().__init__(self.__res_open_fn)
    
    def __res_open_fn(self, name):
        if self.file_path_fn:

            file_path = self.file_path_fn(name)
            self.all_file[name] = file_path
            # print('open', file_path, self.open_opts)
            
            return open(file_path, **self.open_opts)
        else:

            raise ValueError("file_path_fn can't be None")
    
    def set_file_path_fn(self, file_path_fn:callable):
        self.file_path_fn = file_path_fn

        return self

    def get_file(self, name='') -> io.TextIOBase:
        return self.get_res(name)
