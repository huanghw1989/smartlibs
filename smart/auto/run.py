import fire, os, time, logging, sys, json

from smart.utils import AppEnv, dict_deep_merge
from smart.utils.log import auto_load_logging_config, set_default_logging_config
from smart.utils.yaml import yaml_dumps
from smart.utils.signal import set_default_sig_handler

from smart.auto.parser.auto_yml import create_auto_yml_parser_by_module_path
from smart.auto.Runner import AutoRunner
from smart.auto.parser.json_extend import AutoObjJsonEncoder
from smart.auto.parser import cmd_args

from smart.auto.__logger import logger


OPTIONS = {
    'CMD_MODE': False
}


def auto_run(module, name = None, debug_log=None, only_parse=False, rst_format='json',
            lazy_load=True, extra=None, bind_arg=None, delay=0, mp_mode=None, **kwargs):
    """自动化框架

    python -m smart.auto.run <module name> <tree or task> [options] --env.<env_name>=<env_value>

    启用vscode远程调试: python -m smart.auto.run_debug ...

    上述命令可用 smart_auto / smart_auto_debug 替代
    
    Arguments:
        module: auto_yml入口, 用.分割目录; 自动将.转化为路径分隔符并追加.yml后缀
        name: 执行任务名称, 缺省为tree name, 将在yml文件trees节点找到对应任务; 加'task:'前缀可直接执行指定任务
    
    Keyword Arguments:
        debug_log: bool, 是否显示调试日志
        only_parse: bool, 只解析并打印yml配置文件
        rst_format: yml/json/raw/dict, 返回数据格式, 只在 only_parse=True 有效, default: json
        lazy_load: 懒加载任务类文件
        delay: float, 延迟执行(second)
        mp_mode: 多进程模式, 可选: spawn, fork; windows仅支持spawn
        env.xxx: 环境变量
    """
    if set_default_sig_handler():
        logger.debug('set sig_interrupt_handler as default signal handler')
    
    if not name and not only_parse:
        raise 'miss arg: name'

    if mp_mode:
        import multiprocessing
        multiprocessing.set_start_method(mp_mode, True)
        logger.debug('set multiprocessing mode %s', mp_mode)

    runner = None
    
    try:
        envs = cmd_args.set_env_from_args(kwargs)
        bind_arg = cmd_args.resolve_bind_arg(bind_arg, kwargs)

        parser = create_auto_yml_parser_by_module_path(module.strip())
        logger.debug('auto_run yml file: %s', parser.path_ctx.file_path)
        parser.bind_arg(bind_arg)

        run_obj = parser.auto_obj

        if extra:
            run_obj = dict_deep_merge(run_obj, extra, no_copy=True)

        if only_parse:
            if rst_format == 'raw':
                return run_obj

            run_obj_json = json.dumps(run_obj or {}, indent=2, cls=AutoObjJsonEncoder)

            if rst_format == 'json':
                return run_obj_json
            
            rst_val = json.loads(run_obj_json)

            if rst_format in ('yml', 'yaml'):
                rst_val = yaml_dumps(rst_val, indent=2)

            return rst_val
        
        if delay:
            delay = int(delay)
            logger.debug('auto_run %s %s delay %d second', module, name, delay)
            time.sleep(delay)
            
        runner = AutoRunner(run_obj, debug_log=debug_log, lazy_load=lazy_load)
        if isinstance(name, (tuple, list)):
            for sub_name in name:
                runner.start(sub_name)
        else:
            runner.start(name)

        return runner.context.response().to_dict()
    except KeyboardInterrupt:

        logger.info('auto_run end(KeyboardInterrupt)')
    finally:

        AppEnv.clean()

        if runner:
            runner.context.close()


def __detect_logger_level():
    from .__logger import logger_loader, logger_trace

    if not logger.isEnabledFor(logging.DEBUG):
        logger.info('logger auto debug log is disable, you can enable it by logging.yml')
        return

    loggers = (
        logger_loader, logger_trace
    )
    disable_names = []

    for _logger in loggers:
        if not _logger.isEnabledFor(logging.DEBUG):
            disable_names.append(_logger.name)

    if disable_names:
        logger.debug('logger %s debug_level is disable, you can enable it by logging.yml', disable_names)


def main():
    OPTIONS['CMD_MODE'] = True
    auto_load_logging_config() or set_default_logging_config()

    __detect_logger_level()

    fire.Fire(auto_run)


def cmd_ep():
    if sys.path[0] != '':
        sys.path.insert(0, '')
    main()


if __name__ == "__main__":
    main()