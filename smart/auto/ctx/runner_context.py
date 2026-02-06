

class WithAutoRunner:
    @property
    def auto_runner(self):
        return getattr(self, '_auto_runner', None)
    
    @auto_runner.setter
    def auto_runner(self, runner):
        self._auto_runner = runner