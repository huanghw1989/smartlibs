"""
python3 -m tests.utils.run_util_file test_fm
"""
import json, time, io

from smart.utils.file import *
from smart.utils.path import path_join


def item_iter_fn(n=50):
    for i in range(n):
        yield "ab"[i % 2], {
            'id': i,
            'val': '1234567890'[i%9:i%9+1+i%2+i%5+i%7],
            'ts': time.time(),
        }


def test_fm(work_dir='logs/tmp', file_pattern="test_fm_{}.txt"):
    file_path_fn = lambda name: path_join(
        work_dir, file_pattern.format(name), auto_mkdir=True
    )

    fm = FileManage(file_path_fn, open_opts={
        'mode': 'w'
    })

    with fm:
        for name, item in item_iter_fn():
            stream = fm.get_file(name)
            stream.write(json.dumps(item, ensure_ascii=False))
            stream.write('\n')

    print('test_fm save: ', json.dumps(fm.all_file))


def test_res_manage(work_dir='logs/tmp', file_pattern="test_res_manage_{}.txt"):
    all_file = {}
    def res_open_fn(name):
        file_path = path_join(work_dir, file_pattern.format(name))
        all_file[name] = file_path
        return open(file_path, mode='w', encoding='utf8')

    resm = ResManage(res_open_fn)
    with resm:
        for name, item in item_iter_fn():
            stream:io.TextIOBase = resm.get_res(name)
            stream.write(json.dumps(item, ensure_ascii=False))
            stream.write('\n')
    print('test_res_manage save: ', json.dumps(all_file))

if __name__ == "__main__":
    import fire
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })