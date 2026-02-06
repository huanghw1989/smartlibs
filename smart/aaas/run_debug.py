from smart.utils.remote_debug import enable_remote_debug


def cmd_ep():
    import sys

    if sys.path[0] != '':
        sys.path.insert(0, '')
        
    main()


def main():
    enable_remote_debug()

    import multiprocessing as mp
    mp.set_start_method('spawn', True)

    from .run import main as run_main
    run_main()


if __name__ == "__main__":
    main()