import fire, os, sys, time

import multiprocessing as mp

from smart.utils.log import auto_load_logging_config, set_default_logging_config
from smart.utils import AppEnv
from smart.utils.signal import set_default_sig_handler

from smart.auto.parser import cmd_args

from smart.aaas.Runner import ServiceRunner
from smart.aaas.__logger import logger
from .config import smart_env


def run_aaas(port=80, worker_num=None, mp_mode=None, shuttable=False, task_log=None, **kwargs):
    """启动自动化服务
    
    Keyword Arguments:
        port: 端口, 缺省80
        worker_num: 工作进程数
        mp_mode: 多进程模式, 可选: spawn, fork; windows仅支持spawn
        shuttable: 可通过客户端控制aaas服务关闭, 缺省 False; 生产环境不建议启用
        task_log: 任务日志输出, 缺省 None 表示关闭; 也可通过smart_env.yml配置aaas.task_log.dir_path启用
        env.auto_m_clean_timing: 清理完成任务的定时任务间隔, 单位: second, 最小值: 5
        env.auto_m_task_info_ttl: 完成任务的存活时间, 单位: second, 最小值: 5
    """
    if set_default_sig_handler():
        logger.debug('set sig_interrupt_handler as default signal handler')
        
    if worker_num: 
        AppEnv.set('AUTO_WORKER_NUM', worker_num)
    
    if mp_mode:
        mp.set_start_method(mp_mode, True)
        logger.debug('set multiprocessing mode %s', mp_mode)

    if task_log:
        smart_env.set(('task_log', 'dir_path'), task_log)
    
    if shuttable:
        AppEnv.set('AAAS_REMOTE_SHUTTABLE', 1)
    
    if AppEnv.get('AAAS_REMOTE_SHUTTABLE'):
        shuttable = True
        logger.warning('remote shut_down is enabled, you should disable it in production environment')
    else:
        shuttable = False
    
    cmd_args.set_env_from_args(kwargs)
    runner = None

    try:
        pid = os.getpid()
        logger.info('start aaas pid=%s, port=%s', pid, port)
        
        runner = ServiceRunner(port=port)

        if shuttable:
            runner.enable_remote_shuttable()
        
        runner.daemon()
    except KeyboardInterrupt as e:

        logger.info('End aaas (KeyboardInterrupt)')
    else:

        logger.info('End aaas')
    finally:

        if runner:
            runner.auto_manage.close()


def main():
    auto_load_logging_config() or set_default_logging_config()
    fire.Fire(run_aaas)


def cmd_ep():
    if sys.path[0] != '':
        sys.path.insert(0, '')
    main()


if __name__ == "__main__":
    main()