import multiprocessing as mp
from multiprocessing.pool import Pool as BasePool


class NoDaemonProcess(mp.Process):
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


class NoDaemonContext(type(mp.get_context())):
    Process = NoDaemonProcess

# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class Pool(BasePool):
    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super(Pool, self).__init__(*args, **kwargs)