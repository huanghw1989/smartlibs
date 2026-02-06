# python3 -m tests.aaas.test_client log
# python3 -m tests.aaas.test_client log --tail_mode=1 --tail_line=2 --tail_follow=1
# python3 -m tests.aaas.test_client log_cat None more_all --module 'tests.aaas.unitest' --task_name test_mp
# python3 -m tests.aaas.test_client log_cat 45d8ac36720c11ed904dacde48001122 more_all --module 'tests.aaas.unitest' --task_name test_mp --backward=True --log_offset=5419
import pprint, time

from smart.aaas.client import *
from smart.utils.iter import iter_add

from tests.aaas import logger


def __get_client(ep=None, module=None, task_ns=None, **kwargs):
    ep = ep or 'http://127.0.0.1:80'
    module = module or 'starter.aaas.client'
    namespace = task_ns or 'test'
    client = AaasClient(
        entrypoint=ep,
        namespace=namespace
    )

    return client.set_module(module)

def test_asdl(**kwargs):
    client = __get_client(**kwargs)

    asdl = client.asdl()

    logger.info('ASDL:')
    pprint.pprint(asdl)


def test_task(task_name=None, task_delay=3, end_task=False, **kwargs):
    client = __get_client(**kwargs)

    task_name = task_name or 'task:tools__tool.range~@tools__print.item_iter'

    create_task_rst = client.create_task(
        task_name = task_name,
        run_opts = {
            'delay': task_delay
        }
    )

    logger.info('\ncreate_task: %s', create_task_rst)

    task_id = create_task_rst.get('task_id')

    all_task_info = client.all_task()
    logger.info('\nall_task_info:')
    pprint.pprint(all_task_info)

    if task_id:
        task_info = client.task_info(task_id)
        logger.info('\ntask_info: %s', task_info)
    
    if end_task:
        
        end_rst = client.end_task(task_id)
        logger.info('\nend_rst: %s', end_rst)
        time.sleep(.5)
        task_info = client.task_info(task_id)
        logger.info('\ntask_info (after end): %s', task_info)
    elif task_delay:

        time.sleep(task_delay+.5)
        task_info = client.task_info(task_id)
        logger.info('\ntask_info (after sleep): %s', task_info)


def test_info(task_id=None, **kwargs):
    client = __get_client(**kwargs)
    info = client.task_info(task_id)
    logger.info("task_info: ")
    pprint.pprint(info)


def test_log(task_id=None, pool_interval:int=10, pool_line:int=10, log_offset:int=0, 
                tail_mode:bool=False, tail_line:int=100, tail_follow:bool=False, 
                task_name=None, task_delay=3, **kwargs):
    client = __get_client(**kwargs)
    if task_id is None:
        task_name = task_name or 'task:tools__tool.range~@tools__print.item_iter'
        create_task_rst = client.create_task(
            task_name = task_name,
            run_opts = {
                'delay': task_delay
            }
        )
        logger.info('\ncreate_task: %s', create_task_rst)
        task_id = create_task_rst.get('task_id')
    logger.info("task_id: %s", task_id)
    resp = client.task_log(task_id, 
        pool_interval=pool_interval, 
        pool_line=pool_line, 
        log_offset=log_offset,
        tail_mode=tail_mode,
        tail_line=tail_line, 
        tail_follow=tail_follow
    )
    headers = resp.get('headers')
    info = resp.get('info')
    line_iter = resp.get('line_iter')
    logger.info("headers: %s", headers)
    logger.info("info: %s", info)
    logger.info("lines: ")
    for i, line in enumerate(line_iter or []):
        logger.info("%d\t%s", i, line)


def test_log_cat(task_id=None, fn_name='more', follow=True, tail_line:int=10, 
            pool_interval:int=10, pool_line:int=10, backward=False, log_offset:int=None,
            task_name=None, task_delay=3, **kwargs):
    client = __get_client(**kwargs)
    if task_id is None:
        task_name = task_name or 'task:tools__tool.range~@tools__print.item_iter'
        create_task_rst = client.create_task(
            task_name = task_name,
            run_opts = {
                'delay': task_delay
            }
        )
        logger.info('\ncreate_task: %s', create_task_rst)
        task_id = create_task_rst.get('task_id')
    logger.info("task_id: %s", task_id)
    cat = AaasLogCat(client=client, task_id=task_id, pool_interval=pool_interval, pool_line=pool_line)
    cat._debug = True
    line_iter = None
    if log_offset is not None:
        cat.seek(log_offset)
    if fn_name == 'more_all':
        line_iter = cat.more_all(follow=follow, backward=backward)
    elif fn_name == 'tail':
        line_iter = cat.tail(line=tail_line, follow=follow)
    elif fn_name == 'tail_all':
        line_iter = cat.tail_all(line=tail_line, follow=follow)
    elif fn_name == 'backward':
        def _line_iter_fn():
            logger.info("task ended, len(tail_all)=%s", len(list(cat.tail_all(follow=True)))) # 等待任务结束再开始测试从后向前读取数据
            for line_data in reversed(list(cat.tail(line=tail_line))):
                yield line_data
            while True:
                i = 0
                for line_data in cat.more(backward=True):
                    yield line_data
                    i += 1
                if i == 0:
                    break
        line_iter = _line_iter_fn()
    else:
        line_iter = cat.more(follow=follow, backward=backward)
    logger.info("lines: ")
    for i, line in enumerate(line_iter or []):
        logger.info("%d\t%s", i, line)



if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)