from smart.utils import env_eval_str, AppEnv, dict_pop, tuple_fixed_len

from smart.auto.__logger import logger_trace


def pop_args(kwargs, key_prefix):
    filtered = dict_pop(kwargs, lambda k,v: k.startswith(key_prefix))

    return dict(
        (k[len(key_prefix):], v)
        for k, v in filtered.items()
    )


def set_env_from_args(kwargs, pop_env_key=True, env_prefix='env.'):
    envs = pop_args(kwargs, env_prefix)

    for key, val in envs.items():
        envs[key] = env_eval_str(val, expanduser=True, silence=True)
        AppEnv[key] = envs[key]
    
    logger_trace.debug('set_env_from_args %s', envs)

    return envs


def resolve_bind_arg(bind_arg, kwargs, kwargs_prefix='bind_arg.'):
    """解析bind_arg参数
    
    Arguments:
        bind_arg {dict} -- request param bind_arg
        kwargs {dict} -- request param kwargs or cmd flags
    
    Returns:
        dict -- merged bind_arg dict(task_key:arg_dict)
    """
    bind_arg = bind_arg if isinstance(bind_arg, dict) else {}
    cmd_bind_arg = pop_args(kwargs, kwargs_prefix)

    for bind_key, bind_val in cmd_bind_arg.items():
        task_key, arg_name = tuple_fixed_len(bind_key.rsplit('.', 1), 2)

        if not arg_name or not task_key: 
            continue

        if not isinstance(bind_arg.get(task_key), dict): 
            bind_arg[task_key] = {}
            
        bind_arg[task_key][arg_name] = bind_val
    
    return bind_arg
