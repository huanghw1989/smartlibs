

class BaseInterceptor:
    def pre_handle(self) -> bool:
        return True

    def after_handle(self):
        pass

    def after_complete(self):
        pass
