import signal, sys


def sig_interrupt_handler(signum, frame):
    raise KeyboardInterrupt


def sig_exit_handler(signum, frame):
    sys.exit()


def set_default_sig_handler(signum=None, default_handler=None):
    """设置缺省的信号处理函数

    Tip: jupyter需执行 set_default_sig_handler(), smart_auto和smart_aaas进程才能被正确关闭

    Keyword Arguments:
        signum {signal.Signals} -- 枚举值 (default: {signal.SIGINT})
        default_handler {callable} -- 缺省信号处理函数 (default: {sig_interrupt_handler})

    Returns:
        bool -- True表示修改了handler, False表示未修改
    """
    if signum is None:
        signum = signal.SIGINT

    if default_handler is None:
        default_handler = sig_interrupt_handler

    curr_handler = signal.getsignal(signum)

    if curr_handler is None or curr_handler == signal.Handlers.SIG_IGN:
        signal.signal(signum, default_handler)
        
        return True
    else:
        return False