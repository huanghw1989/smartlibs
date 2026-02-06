

class UnSupport:
    def __init__(self, feature=None, tip=None) -> None:
        self.feature = feature
        self.tip = tip

    def __err(self):
        msgs = [
            'UnSupport ' + self.feature or 'feature',
            self.tip or None
        ]
        return Exception(", ".join(filter(None, msgs)))

    def __call__(self, *args, **kwds):
        raise self.__err()

    def __getattr__(self, name:str):
        if name.startswith('__'):
            return object.__getattribute__(self, name)
        raise self.__err()