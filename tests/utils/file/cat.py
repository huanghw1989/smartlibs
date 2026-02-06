# python3 -m tests.utils.file.cat safe_seek_read_text
# python3 -m tests.utils.file.cat readline_up
# python3 -m tests.utils.file.cat readline_up 2 --file_mode w+
# python3 -m tests.utils.file.cat readline_up 2 --file_mode w+ --tail_offset 3
# python3 -m tests.utils.file.cat more
# python3 -m tests.utils.file.cat more 0 3 --file_mode=w+
# python3 -m tests.utils.file.cat more -1 --file_mode=w+ --tail_mode=True
# python3 -m tests.utils.file.cat more 0 -3 --file_mode=w+ --tail_mode=True
# python3 -m tests.utils.file.cat tail 2 --file_mode=w+
# python3 -m tests.utils.file.cat tail 2
# python3 -m tests.utils.file.cat tail 0 3 --file_mode=w+
# python3 -m tests.utils.file.cat tail_f --num_line=3 --follow_max_time=10
# python3 -m tests.utils.file.cat tail_f --num_line=3 --follow_max_time=10 --file_mode='r'
from smart.utils.file.cat import *
from tempfile import TemporaryFile
from tests.utils import logger
import json, sys


def _temp_file(text, file_mode):
    tmp_file = TemporaryFile(mode=file_mode)
    if file_mode[-1] == 'b':
        tmp_file.write(text.encode("utf8"))
    else:
        tmp_file.write(text)
    return tmp_file

def test_safe_seek_read_text(file_mode:str='w+'):
    text_list = [
        # """0123\n456\n789""", 
        """啊123\n456哦\n789"""
    ]
    for i, text in enumerate(text_list):
        logger.info("###text-%s-->\n%s", i, json.dumps(text, ensure_ascii=False))
        tmp_file = _temp_file(text, file_mode)
        len_b = len(text.encode("utf8"))
        for i in range(0, len_b-2, 1):
            data, fix_seek_pos, fix_pos_end = fp_safe_seek_read_text(tmp_file, i, byte_size=3)
            data2 = json.dumps(data, ensure_ascii=False) if isinstance(data, str) else data
            logger.info("pos=%s, data: %s, fix_pos=%s", i, data2, (fix_seek_pos, fix_pos_end))


def test_readline_up(num_line:int=2, buffer_size:int=2, file_mode:str='w+b', tail_offset:int=None):
    text_list = [
        """0123\n456\n789""", 
        """啊123\n456哦\n789""",
        """啊123\n456哦\n789\n\n"""
    ]
    for i, text in enumerate(text_list):
        logger.info("###text-%s-->\n%s", i, json.dumps(text, ensure_ascii=False))
        tmp_file = _temp_file(text, file_mode)
        if tail_offset:
            seek_pos = max(tmp_file.tell() - tail_offset, 0)
            tmp_file.seek(seek_pos)
        reader = FileReadlineUp(tmp_file, buffer_size=buffer_size)
        reader.buffer_size = buffer_size
        logger.info("readline_up-->")
        for line in reader.readline_up(int(num_line)):
            logger.info("[%s] %s", type(line).__name__, json.dumps(line, ensure_ascii=False) if isinstance(line, str) else line)
        pos1 = tmp_file.tell()
        reader.fix_seek()
        pos2 = tmp_file.tell()
        next_ch = fp_safe_seek_read_text(tmp_file, pos2, 1)
        logger.info("pos before fix=%s, after fix=%s, reader._rest_data: %s, %s, next_ch(after fix)=%s", pos1, pos2, reader._rest_data, reader._curr_pos, next_ch)
        tmp_file.close()

def test_more(num_line=1, num_byte=None, tail_mode:bool=False, file_mode:str='w+b', more_times:int=None):
    text_list = [
        """0123\n456\n789""", 
        """啊123\n456哦\n789""",
    ]
    for i, text in enumerate(text_list):
        logger.info("###text-%s-->\n%s", i, json.dumps(text, ensure_ascii=False))
        tmp_file = _temp_file(text, file_mode)
        cat = FileCat(tmp_file)
        if tail_mode:
            cat.seek_tail()
        else:
            cat.seek(0)
        for _ in range(more_times or sys.maxsize):
            lines = list(cat.more(num_line=num_line, num_byte=num_byte))
            for i, line in enumerate(lines):
                logger.info("%s: %s", i, json.dumps(line, ensure_ascii=False) if isinstance(line, str) else line)
            if not len(lines):
                break

def test_tail(num_line=1, num_byte=None, file_mode:str='w+b'):
    text_list = [
        """0123\n456\n789""", 
        """啊123\n456哦\n789""",
        """啊123\n456哦\n789\n\n"""
    ]
    for i, text in enumerate(text_list):
        logger.info("###text-%s-->\n%s", i, json.dumps(text, ensure_ascii=False))
        tmp_file = _temp_file(text, file_mode)
        cat = FileCat(tmp_file)
        cat.seek(0)
        lines_iter = cat.tail(num_line=num_line, num_byte=num_byte)
        for i, line in enumerate(lines_iter):
            logger.info("%s: %s", i, json.dumps(line, ensure_ascii=False) if isinstance(line, str) else line)

def test_tail_f(file_path='logs/smartx.log', num_line=1, num_byte=None, file_mode:str='rb', 
            follow_num_byte:int=None, follow_max_time:int=None, follow_line_mode=False):
    logger.info("tail_f file_path: %s, %s", file_path, file_mode)
    with open(file_path, mode=file_mode) as fp:
        cat = FileCat(fp)
        data_iter = cat.tail(num_line=num_line, num_byte=num_byte, follow=True, 
            follow_num_byte=follow_num_byte, follow_max_time=follow_max_time, follow_line_mode=follow_line_mode)
        for i, data in enumerate(data_iter):
            data2 = json.dumps(data, ensure_ascii=False) if isinstance(data, str) else data
            logger.info("%s: %s", i, data2)


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)