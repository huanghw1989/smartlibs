### Run Examples
# uwsgi --http :8081 --processes 1 --threads 4 --module "smart.aaas.wsgi:app()" --pyargv "--worker_num 10"
# uwsgi --http :8081 --processes 1 --threads 4 --stats 127.0.0.1:8082 --module "smart.aaas.wsgi:app()"
import argparse
import multiprocessing as mp

from smart.aaas.Runner import ServiceRunner
from smart.utils.log import auto_load_logging_config, set_default_logging_config
from smart.utils import AppEnv
from smart.aaas.__logger import logger
from smart.aaas.config import smart_env

auto_load_logging_config() or set_default_logging_config()

parser = argparse.ArgumentParser()
parser.add_argument("-w", "--worker_num", dest='worker_num', default=4, help="工作进程数")
parser.add_argument("--mp_mode", dest='mp_mode', default=None, help="多进程模式, 可选: spawn, fork; windows仅支持spawn")
parser.add_argument("--task_log", dest='task_log', default=None, help="任务日志输出的目录, 缺省 None 表示关闭")

args = parser.parse_args()


def app():
    worker_num = args.worker_num
    if worker_num: 
        AppEnv.set('AUTO_WORKER_NUM', worker_num)

    if args.mp_mode:
        mp.set_start_method(args.mp_mode, True)
        logger.debug('set multiprocessing mode %s', args.mp_mode)

    if args.task_log:
        smart_env.set(('task_log', 'dir_path'), args.task_log)

    _app = ServiceRunner()
    _app.start(wsgi_mode=True)
    return _app.wsgi


def app_debug():
    wsgi_fn = app()
    def _wsgi_fn(*args):
        from smart.utils.remote_debug import enable_remote_debug
        enable_remote_debug()
        return wsgi_fn(*args)
    return _wsgi_fn