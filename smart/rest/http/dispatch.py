# import threading
# from ..__logger import logger_rest
from ..app.dispatch import ServiceDispatcher


class RestHttpDispatcher(ServiceDispatcher):
    def __init__(self, app=None, **kwargs):
        super().__init__(app, **kwargs)

    def dispatch(self, http_method, request):
        # request.context['_thread_name'] = thread_name = threading.current_thread().name
        # logger_rest.debug("RestHttpDispatcher.dispatch %s", request.client_address)
        return super().dispatch(http_method, request)
