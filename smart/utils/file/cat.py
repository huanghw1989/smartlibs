import io, time


def fp_readline(fp:io.IOBase, num:int):
    """向后读取n行数据

    Args:
        fp (io.IOBase): 文件流, open函数的返回值
        num (int): 行数, None表示读取所有行

    Yields:
        bytes|str: 读取的行数据
    """
    i = 0
    while True:
        line = fp.readline()
        if not line:
            break
        yield line
        i += 1
        if num and i >= num:
            break


def fp_safe_seek_read_text(fp:io.IOBase, seek_pos:int, byte_size:int=None, read_size:int=None, 
            retry_num:int=5, encoding='utf8'):
    """文本类型的文件流, seek到指定位置并读取若干字节数据

    utf8编码的中文, 字节长度为3; fp.seek函数是按字节位置移动指针, fp.read函数是按文本长度读取数据; 
    所以seek和read组合使用存在2个问题, seek到中文的非首字节数据时, read函数会出现UnicodeDecodeError异常;
    第二个问题是read的结果很难控制指定的字节长度; 本函数解决这两个问题。

    Args:
        fp (io.IOBase): 文件流, open函数的返回值
        seek_pos (int): seek到指定位置读取
        byte_size (int): 读取的字节长度
        read_size (int): 读取的文本长度
        retry_num (int, optional): 出现编码错误时向前搜索到次数, 至少取3. Defaults to 5.
        encoding (str, optional): 字符编码. Defaults to 'utf8'.

    Returns:
        tuple: (data, fixed_seek_pos, fixed_end_pos) fixed_seek_pos是seek_pos向前修正到中文首字节位置
    """
    _read_size = read_size or byte_size
    assert _read_size and _read_size > 0
    use_byte_size = not read_size

    for i in range(retry_num):
        try:
            fixed_seek_pos, _size = seek_pos-i, _read_size+i
            if fixed_seek_pos>=0:
                fp.seek(fixed_seek_pos)
                fix_data = data = fp.read(_size)
                _fix_size = _size
                fixed_end_pos = None
                if isinstance(data, str) and use_byte_size:
                    # 字符串类型按字节长度读取时，需修正
                    bin_data = data.encode(encoding)
                    for j in range(retry_num):
                        _fix_size = _size+j
                        try:
                            fix_data = bin_data[:_fix_size].decode(encoding)
                            fixed_end_pos = fixed_seek_pos+_fix_size
                            break
                        except UnicodeDecodeError:
                            pass
                if fixed_end_pos is None:
                    fixed_end_pos = fp.tell()
                return fix_data, fixed_seek_pos, fixed_end_pos
            else:
                return None, None, None
        except UnicodeDecodeError:
            pass
    return None, None, None


class FileReadlineUp:
    def __init__(self, fp:io.IOBase, buffer_size:int=1024, text_mode:bool=None, text_encoding:str=None) -> None:
        """文件向上读取行

        Args:
            fp (io.IOBase): 文件流, open函数的返回值
            buffer_size (int, optional): 向前seek的间隔. Defaults to 1024.
            text_mode (bool, optional): 是否文本模式, None会根据fp自动判断, False表示binaray. Defaults to None.
            text_encoding (str, optional): 文本编码, None会根据fp自动判断. Defaults to None.
        """
        if text_mode is None:
            # 根据fp自动判断是否文本类型
            text_mode = type(fp.read(0)) == str
        if text_mode and text_encoding is None:
            # 根据fp的encoding设置text_encoding
            text_encoding = getattr(fp, 'encoding', 'utf8')
        self.fp = fp
        self.buffer_size = max(buffer_size or 0, 100)
        self.text_mode = text_mode
        self.text_encoding = text_encoding
        self._rest_data = None
    
    def readline_up(self, num:int):
        """从后向前读取n行, 起始位置为fp当前指针位置

        Args:
            num (int): 行数

        Yields:
            bytes|str: 读取的行数据
        """
        if not num or num < 0:
            return

        size, text_mode = self.buffer_size, self.text_mode
        fp = self.fp
        curr_pos = fp.tell()
        _nl = '\n' if text_mode else b'\n'[0] # 根据数据类型设置换行符
        count = 0
        rest_data = None
        while True:
            seek_pos = max(curr_pos-size, 0)
            byte_size = curr_pos-seek_pos
            if byte_size <= 0:
                # no more data
                break
            # 向前读取数据
            if text_mode:
                # text mode
                data, fixed_seek_pos, fixed_end_pos = fp_safe_seek_read_text(fp, seek_pos, byte_size=byte_size, encoding=self.text_encoding)
                if fixed_seek_pos is not None:
                    seek_pos = fixed_seek_pos
                else:
                    # 无法向前读取数据
                    break
            else:
                # binary mode
                fp.seek(seek_pos)
                data = fp.read(byte_size)
    
            len_data = len(data) # 不包含rest_data的长度
            if rest_data:
                data = data + rest_data
            prev_split = len(data) # 包含rest_data的长度
            for i in range(len_data-1, -1, -1):
                if data[i] == _nl:
                    split = i+1
                    if split < prev_split:
                        # 遇到换行符，返回换行符之后的数据
                        yield data[split:prev_split]
                        count += 1
                        if count >= num:
                            prev_split = split
                            break
                    prev_split = split
            rest_data = data[:prev_split]
            curr_pos = seek_pos
            if count >= num:
                break
        if curr_pos == 0 and count < num and rest_data:
            # 已到文件头部, 还有剩余数据且未到达行数时, 返回剩余数据
            yield rest_data
            rest_data = None
            curr_pos = 0
        self._rest_data = rest_data
        self._curr_pos = curr_pos
    
    def fix_seek(self):
        """将文件指针移动到向前n行数据的起始位置
        """
        _rest_data = self._rest_data
        if _rest_data:
            if type(_rest_data) == str:
                _rest_data == _rest_data.encode(self.text_encoding)
            seek_pos = self._curr_pos+len(_rest_data)
        else:
            seek_pos = self._curr_pos
        self.fp.seek(seek_pos)


class FileCat:
    DEFAULT_NUM_LINE = 10
    DEFAULT_BUFFER_SIZE = 1024
    DEFAULT_FOLLOW_INTERVAL = 1.0
    MIN_FOLLOW_INTERVAL = 0.5

    def __init__(self, fp:io.IOBase, text_mode:bool=None, text_encoding:str=None, opts:dict=None) -> None:
        """文件查看的工具类

        Args:
            fp (io.IOBase): 文件流, open函数的返回值
            text_mode (bool, optional): 是否文本模式, None会根据fp自动判断, False表示binaray. Defaults to None.
            text_encoding (str, optional): 文本编码, None会根据fp自动判断. Defaults to None.
            opts (dict, optional): 可选配置项有{num_line, buffer_size, follow_interval}. Defaults to None.
        """
        self.fp = fp
        if text_mode is None:
            # 根据fp自动判断是否文本类型
            text_mode = type(fp.read(0)) == str
        if text_mode and text_encoding is None:
            # 根据fp的encoding设置text_encoding
            text_encoding = getattr(fp, 'encoding', 'utf8')
        self.text_mode = text_mode
        self.text_encoding = text_encoding
        self.opts = {
            'num_line': self.DEFAULT_NUM_LINE,
            'buffer_size': self.DEFAULT_BUFFER_SIZE,
            'follow_interval': self.DEFAULT_FOLLOW_INTERVAL
        }
        if opts:
            self.opts.update(opts)
    
    def tell(self):
        """文件的当前指针位置

        Returns:
            int: 文件指针位置
        """
        return self.fp.tell()

    def seek(self, *args):
        """移动文件指针位置

        移动到文件末尾: seek(0, 2)
        移动到第10个字节: seek(10)

        Returns:
            int: 移动后的文件指针位置
        """
        return self.fp.seek(*args)
    
    def seek_tail(self, offset:int=0):
        """移动到文件末尾

        Args:
            offset (int, optional): 末尾向前多少字节. Defaults to 0.

        Returns:
            int: 移动后的文件指针位置
        """
        len = self.seek(0, 2)
        if offset:
            pos = max(len-offset, 0)
            return self.seek(pos)
        return len
    
    def head(self, num_line:int=None, num_char:int=None):
        """从头部开始取数据

        Args:
            num_line (int, optional): 前多少行. Defaults to None.
            num_char (int, optional): 前多少字节, 非空时忽略num_line. Defaults to None.

        Yields:
            bytes|str: 读取的行数据/指定字节数据
        """
        self.seek(0)
        if num_char is not None:
            data = self.fp.read(num_char)
            if data:
                yield data
            return

        if num_line is None:
            num_line = self.opts.get('num_line')
        yield from fp_readline(self.fp, num_line)

    def tail(self, num_line:int=0, num_byte:int=None, follow=False, follow_line_mode:bool=False, follow_num_byte:int=None, 
            follow_max_time:float=None, follow_expire_at:float=None, follow_is_end_fn:callable=None):
        """从文件末尾取数据

        Args:
            num_line (int, optional): 从末尾向前读取num_line行, 按正序返回. Defaults to 0.
            num_byte (int, optional): 从末尾向前读取num_byte字节; num_line非空时, num_byte无效. Defaults to None.
            follow (bool, optional): 达到文件末尾后, 是否向后按一定时间间隔(缺省0.5)读取新增数据. Defaults to False.
            follow_line_mode (bool, optional): 是否按行取走最新增加的数据. Defaults to False.
            follow_num_byte (int, optional): 每次取follow_num_byte长度的数据, 当follow_line_mode=True时本参数无效. Defaults to None.
            follow_max_time (float, optional): 多少秒之后停止取新数据. Defaults to None.
            follow_expire_at (float, optional): 时间戳在follow_expire_at之后停止取新数据. Defaults to None.
            follow_is_end_fn (callable, optional): 文件无新数据时执行回调函数, 函数返回True表示停止取数. Defaults to None.

        Yields:
            bytes: 读取的文件数据, 包含换行符
        """
        ts_begin = time.time()
        if not follow_expire_at and follow_max_time:
            follow_expire_at = ts_begin + follow_max_time
        tail_pos = None
        if num_line:
            tail_pos = self.seek_tail()
            tail_data = list(self._more_line(-num_line))
            yield from reversed(tail_data)
        elif num_byte:
            tail_pos = self.seek_tail()
            tail_data = list(self._more_byte(-num_byte))
            yield from reversed(tail_data)

        if follow:
            fp = self.fp
            follow_interval = max(self.MIN_FOLLOW_INTERVAL, self.opts.get('follow_interval'))
            self.seek_tail() if tail_pos is None else self.seek(tail_pos)
            prev_line = None
            while True:
                if follow_line_mode:
                    # 按行取走最新增加的数据
                    _nl = '\n' if self.text_mode else b'\n'[0] # 根据数据类型设置换行符
                    for line in fp_readline(fp, None):
                        if line and line[-1] == _nl:
                            if prev_line:
                                yield prev_line + line
                                prev_line = None
                            else:
                                yield line
                        else:
                            # 已到达文件末尾, 最后一个换行符之后的数据暂存在prev_line, 等待下次循环拼接数据
                            prev_line = (prev_line + line) if prev_line and line else (prev_line or line)
                else:
                    if follow_num_byte and follow_num_byte > 0:
                        while True:
                            # 每次取follow_num_byte长度的数据, 直至无数据
                            data = list(self._more_byte(follow_num_byte))
                            if len(data):
                                yield from data
                            else:
                                break
                    else:
                        # 一次性取走新增的所有数据
                        data = fp.read()
                        if data:
                            yield data
                ts_curr = time.time()
                if ts_curr >= follow_expire_at:
                    break
                if follow_is_end_fn and follow_is_end_fn():
                    break
                # 间隔follow_interval秒，等待新数据
                time.sleep(follow_interval)

    def _more_byte(self, num_byte):
        fp = self.fp
        if self.text_mode and num_byte > 0:
            # str文件流 - 向后读取指定字节长度的数据
            data, fixed_seek_pos, fixed_end_pos  = fp_safe_seek_read_text(
                fp, fp.tell(), byte_size=num_byte, encoding=self.text_encoding)
            if data:
                yield data
            if fixed_end_pos:
                fp.seek(fixed_end_pos)
        elif not self.text_mode and num_byte > 0:
            # byte文件流 - 向后读取指定字节长度的数据
            data = fp.read(num_byte)
            if data:
                yield data
        elif self.text_mode:
            # str文件流 - 向前读取指定字节长度的数据, num_byte为负数
            curr_pos = fp.tell()
            seek_pos = max(0, curr_pos+num_byte)
            byte_size = curr_pos - seek_pos
            if byte_size <= 0:
                return
            data, fixed_seek_pos, fixed_end_pos  = fp_safe_seek_read_text(
                fp, seek_pos, byte_size=byte_size, encoding=self.text_encoding)
            if data:
                yield data
            if fixed_seek_pos is not None:
                fp.seek(fixed_seek_pos)
        else:
            # byte文件流 - 向前读取指定字节长度的数据, num_byte为负数
            curr_pos = fp.tell()
            seek_pos = max(curr_pos+num_byte, 0)
            if seek_pos != curr_pos:
                fp.seek(seek_pos)
            c = curr_pos-seek_pos
            if c > 0:
                yield fp.read(c)
                fp.seek(seek_pos)
    
    def _more_line(self, num_line):
        fp = self.fp
        if num_line is None:
            num_line = self.opts.get('num_line')

        if num_line > 0:
            # 向后读取n行数据
            yield from fp_readline(fp, num_line)
        else:
            # 向前读取n行数据, num_line为负数
            reader = FileReadlineUp(
                fp, buffer_size=self.opts.get('buffer_size'), 
                text_mode=self.text_mode, text_encoding=self.text_encoding)
            yield from reader.readline_up(-num_line)
            reader.fix_seek()

    def more(self, num_line:int=None, num_byte:int=None):
        """分页读取文件数据

        num_byte为负数时, 向前读取若干字节的数据; num_byte为正数时, 向后读取若干字节的数据; 
        num_line为负数时, 向前读取若干行数据; num_line为正数时, 向后读取若干行数据; 

        Args:
            num_line (int, optional): 行数, 正数向后, 负数向前. Defaults to None.
            num_byte (int, optional): 字节数, 非空时忽略num_line参数, 正数向后, 负数向前. Defaults to None.

        Yields:
            bytes|str: 读取的行数据/指定字节数据
        """
        if num_byte:
            yield from self._more_byte(num_byte)
        else:
            yield from self._more_line(num_line)

