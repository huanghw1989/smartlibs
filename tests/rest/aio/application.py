import pickle
import multiprocessing as mp

from smart.rest.aio.application import AsyncServiceApplication


def test_pickle():
    req_queue = mp.Queue()
    app = AsyncServiceApplication(req_queue, None)
    print('worker_pool:', app.worker_pool)
    print('app.__dict__:', app.__dict__)
    print('pickle.dumps:', pickle.dumps(app))


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)