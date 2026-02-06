from typing import Type

class BaseWorker:
    def __init__(self, target, args=(), kwargs=None, name=None) -> None:
        if kwargs is None:
            kwargs = {}
        self._func = target
        self._func_args = args
        self._func_kwargs = kwargs
        self._worker_name = name

    def start(self):
        pass

    def join(self, timeout=None):
        pass

    def is_alive(self):
        pass

    @property
    def ident(self):
        pass

    @property
    def exitcode(self):
        return None

    @property
    def worker_name(self):
        return 'Worker-' + str(self._worker_name or self.ident)

    def safeStop(self):
        pass

    def forceStop(self):
        pass

    def __repr__(self) -> str:
        return self.__class__.__name__ + '-' + str(self.ident) + ('-' + self._worker_name if self._worker_name else '')


def worker_cls_builder(mode=None) -> Type[BaseWorker]:
    if mode == 'thread':
        from .ThreadWorker import ThreadWorker
        return ThreadWorker
    else:
        from .ProcessWorker import ProcessWorker
        return ProcessWorker
