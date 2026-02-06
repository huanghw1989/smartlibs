import os

from smart.utils.bound import BoundFn
from smart.utils.func import func_safe_call

from smart.auto.__logger import logger


class FnItem(BoundFn):
    def __init__(self, func, type=None, name=None):
        BoundFn.__init__(self, func)
        self.fn_type = type
        self.__rst = None
        self._called = False
        self._name = name
    
    @property
    def result(self):
        return self.__rst

    def __call__(self, *args, **kwargs):
        args = [*self.bind_args, *args] if args else self.bind_args
        kwargs = {**self.bind_kwargs, **kwargs} if kwargs else self.bind_kwargs
        
        logger.debug('FnItem %s %s start, pid=%s', self.fn_type, self._name or self.__hash__(), os.getpid())

        self.__rst = rst = func_safe_call(self.__func__, args, kwargs)
        self._called = True
        
        return rst
    
    def call(self, args:list=None, kwargs:dict=None, once=False):
        if once and self._called:
            return self.__rst

        args = [*self.bind_args, *args] if args else self.bind_args
        kwargs = {**self.bind_kwargs, **kwargs} if kwargs else self.bind_kwargs
        logger.debug('FnItem %s %s start, pid=%s', self.fn_type, self._name or self.__hash__(), os.getpid())
        self.__rst = rst = func_safe_call(self.__func__, args, kwargs)
        self._called = True
        return rst


class FnBlock:
    def __init__(self):
        self._fn_items = []
    
    def add_item(self, fn_item: FnItem):
        if fn_item and isinstance(fn_item, FnItem):
            self._fn_items.append(fn_item)
    
    def run_block(self, fn_args=[], fn_kwargs={}, fn_filter=None, once=False):
        block_rst = {}

        for fn_item in self._fn_items:
            fn_item:FnItem
            b_run = fn_filter and fn_filter(fn_item)

            if b_run:
                fn_rst = fn_item.call(fn_args, fn_kwargs, once=once)
            else:
                fn_rst = fn_item.result
            
            if fn_rst and isinstance(fn_rst, dict):
                block_rst.update(fn_rst)
        
        return block_rst


class FnChain:
    def __init__(self):
        self.__chain = []
    
    def new_block(self):
        fn_block = FnBlock()

        self.__chain.append(fn_block)

        return fn_block
    
    def run_chain(self, fn_filter=None, once=False):
        chain_rst = {}
        
        for fn_block in self.__chain:
            fn_block:FnBlock

            block_rst = fn_block.run_block(
                fn_kwargs=chain_rst,
                fn_filter=fn_filter,
                once=once
            )

            chain_rst.update(block_rst)
        
        return chain_rst
    
