import json


class JsonlFile:
    def __init__(self, all_file:dict, mode, encoding:str='utf8', enter_func=''):
        if isinstance(all_file, str):
            all_file = {'': all_file}

        self.all_file = all_file
        self.opend = {}
        self.mode = mode
        self.encoding = encoding
        self.__enter_func = enter_func

    def __enter__(self):
        for target, file_path in self.all_file.items():
            self.opend[target] = open(file_path, self.mode, encoding=self.encoding)

        if self.__enter_func:
            return getattr(self, self.__enter_func)
        else:
            return self
    
    def auto_open(self, file_path_fn:callable):
        self.file_path_fn = file_path_fn
    
    def get_file(self, target=''):
        if target not in self.opend:
            if self.file_path_fn:

                file_path = self.file_path_fn(target)
                self.all_file[target] = file_path
                self.opend[target] = open(file_path, self.mode, encoding=self.encoding)
            else:

                raise ValueError('no target file: '+target)

        return self.opend[target]
    
    def close(self):
        for target, f in self.opend.items():
            del self.opend[target]
            f.close()

    def __exit__(self, errClass, errMsg, errTrace):
        for target, f in self.opend.items():
            f.close()


class JsonlWriter(JsonlFile):
    """Example:
    with JsonlWriter({'out': './tmp/out.jsonl'}) as write:
        for i in range(5):
            write('out', {'id': i})
    """
    def __init__(self, all_file, mode='w', encoding='utf8', dump_opts = {'ensure_ascii':False}):
        JsonlFile.__init__(self, all_file, mode, encoding, enter_func='write')
        self.dump_opts = dump_opts

    def write(self, target, item):
        f = self.get_file(target)
        f.write(json.dumps(item, **self.dump_opts))
        f.write("\n")


class JsonlReader(JsonlFile):
    """Example:
    with JsonlReader(file_path) as get_items:
        print(list(get_items()))
    """
    def __init__(self, all_file:dict, mode='r', encoding='utf8'):
        JsonlFile.__init__(self, all_file, mode, encoding, enter_func='get_items')

    def get_items(self, target=''):
        f = self.opend[target]

        for line in f:
            line = line.strip()

            if line:
                item = json.loads(line)
                yield item


class JsonlOffsetReader(JsonlReader):
    """Example:
    with JsonlOffsetReader(file_path) as get_items:
        print(list(get_items(offset=1, count=3)))
    """
    def get_items(self, target='', offset=0, count=None):
        f = self.opend[target]
        line_no = 0

        for line in f:
            line_no += 1

            if offset > 0:
                offset -= 1
                continue

            if count is not None:
                count -= 1
                if count < 0:
                    break
                
            item = json.loads(line)
            yield item, line_no