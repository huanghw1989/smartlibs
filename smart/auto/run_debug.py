import os


ENV_DEBUG_PORT = os.environ.get('DEBUG_PORT')
DEBUG_PORT = int(ENV_DEBUG_PORT) if ENV_DEBUG_PORT else 5678


def debug(port=None):
    import ptvsd
    port = port or DEBUG_PORT
    address = ('0.0.0.0', port)
    ptvsd.enable_attach(address)
    print('### Wait Remote Debug (port:' + str(port) + ') ###')
    if not ENV_DEBUG_PORT:
        print('Set env DEBUG_PORT can change port. (Linux example cmd: export DEBUG_PORT=5679)')
    ptvsd.wait_for_attach()
    print('### Connected Remote Debug ###')


# if __name__ == "__main__":
#     debug()


from .run import main as run_main, cmd_ep as run_cmd_ep


def main():
    debug()
    run_main()


def cmd_ep():
    debug()
    run_cmd_ep()


if __name__ == "__main__":
    main()