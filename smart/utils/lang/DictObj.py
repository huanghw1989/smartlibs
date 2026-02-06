from typing import Iterable


class DictObj:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    def __setitem__(self, key, value):
        self.__dict__[str(key)] = value
    
    def __getitem__(self, key):
        return self.__dict__.get(str(key))

    def __iter__(self):
        for key in self.__dict__.keys():
            if key[:1] != "_":
                yield key

    def __repr__(self) -> str:
        return self.__class__.__name__ + '(' + ', '.join(
            str(k)+'='+str(self.__dict__[k]) for k in self.__iter__()
        ) + ')'

    def to_dict(self, keys:Iterable=None):
        if keys:
            return {k:self.__dict__.get(str(k)) for k in keys}
        else:
            return {k:v for k, v in self.__dict__.items() if k[:1] != "_"}