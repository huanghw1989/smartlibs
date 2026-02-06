import os


def enable_remote_debug(port = None):
    """远程调试代码

    代码主动断点: debugpy.breakpoint()

    Args:
        port (int, optional): 调试端口. Defaults to None.
    """
    try:
        import debugpy
        if port is None:
            ENV_DEBUG_PORT = os.environ.get('DEBUG_PORT')
            port = int(ENV_DEBUG_PORT) if ENV_DEBUG_PORT else 5678
            if not ENV_DEBUG_PORT:
                print('Set env DEBUG_PORT can change default port. (Linux example cmd: export DEBUG_PORT=5678)')
        address = ('0.0.0.0', port)
        debugpy.listen(address)
        print('### Wait Remote Debug (port:' + str(port) + ') ###')
        debugpy.wait_for_client()
        print('### Connected Remote Debug ###')
    except BaseException as e:
        print('enable_remote_debug err:', e)
        return False
    else:
        return True


def enable_by_env(env_name='REMOTE_DEBUG', port = None):
    if os.environ.get(env_name):
        enable_remote_debug(port=port)
        return 1
    else:
        return 0


def enable_remote_debug_by_ptvsd(port = None):
    """旧版本vscode通过ptvsd远程调试代码

    Args:
        port (int, optional): 调试端口. Defaults to None.
    """
    try:
        import ptvsd
        if port is None:
            ENV_DEBUG_PORT = os.environ.get('DEBUG_PORT')
            port = int(ENV_DEBUG_PORT) if ENV_DEBUG_PORT else 5678
            if not ENV_DEBUG_PORT:
                print('Set env DEBUG_PORT can change default port. (Linux example cmd: export DEBUG_PORT=5678)')
        address = ('0.0.0.0', port)
        ptvsd.enable_attach(address)
        print('### Wait Remote Debug (port:' + str(port) + ') ###')
        ptvsd.wait_for_attach()
        print('### Connected Remote Debug ###')
    except BaseException as e:
        print('enable_remote_debug err:', e)
        return False
    else:
        return True