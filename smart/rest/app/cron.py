from .crond import Crond, TimingTaskMeta

from ..__logger import logger_rest


def schedule(crontab, args=[], kwargs={}):
    """schedule服务未实现, 请使用 timing
    TODO
    
    Arguments:
        crontab {str} -- linux crontab str
    
    Keyword Arguments:
        args {list} -- 函数执行参数 (default: {[]})
        kwargs {dict} -- 函数执行keyword参数 (default: {{}})
    
    Returns:
        callable -- decorator
    """
    
    def decorator(func:callable):
        logger_rest.debug('schedule %s %s(%s)', crontab, func.__name__, 
            ', '.join([*map(str, args), *[str(k)+'='+str(v) for k, v in kwargs.items()]]))

        Crond.schedule_tasks.append((crontab, func, args, kwargs))

        return func

    return decorator


def timing(interval, args=[], kwargs={}, run_immediate=False):

    def decorator(func:callable):
        nonlocal interval

        logger_rest.debug('Cron Timing Task %s %s(%s)', interval, func.__name__, 
            ', '.join([*map(str, args), *[str(k)+'='+str(v) for k, v in kwargs.items()]]))
        
        Crond.add_timing_task(TimingTaskMeta(
            timing_fn=func,
            timing_fn_args=args,
            timing_fn_kwargs=kwargs,
            interval=interval,
            run_immediate=run_immediate
        ))

        return func

    return decorator
