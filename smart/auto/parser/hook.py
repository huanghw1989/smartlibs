from smart.auto.base import BaseHook


class AutoYmlHook(BaseHook):
    def __init__(self, run_obj):
        self.run_obj = run_obj
    
    def before_parse(self, **kwargs):
        pass

    def after_parse(self, **kwargs):
        pass


class AutoYmlHookManager():
    def __init__(self):
        self.hooks = []
        self.__trigered_event = set()

    def add_hook(self, hook:AutoYmlHook):
        self.hooks.append(hook)

    def triger(self, event_name, **kwargs):
        for hook in self.hooks:
            if callable(hook):
                hook(event_name, **kwargs)

    def triger_once(self, event_name, **kwargs):
        for hook in self.hooks:
            once_key = (event_name, hook)
            if once_key in self.__trigered_event:
                continue
            self.__trigered_event.add(once_key)
            if callable(hook):
                hook(event_name, **kwargs)
