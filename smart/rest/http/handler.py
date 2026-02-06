from http.server import BaseHTTPRequestHandler
from .request import ServiceRequest


class RequestHandler(BaseHTTPRequestHandler):
    @property
    def dispatcher(self):
        return getattr(self, '_dispatcher', None)

    @dispatcher.setter
    def dispatcher(self, dispatcher):
        setattr(self, '_dispatcher', dispatcher)


class DynClassFactory:
    cls_idx = 0

    @staticmethod
    def create(clazz, attrs = None):
        base_name = clazz.__name__
        DynClassFactory.cls_idx += 1
        cls_name = base_name + '_' + str(DynClassFactory.cls_idx)
        return type(cls_name, (clazz,), attrs or {})


def wrap_request_handler(handler_class:BaseHTTPRequestHandler=RequestHandler, dispatcher=None, methods=None):
    if methods is None: methods = [
        'HEAD', 'GET', 'POST', 'PUT', 'OPTIONS', 'DELETE'
    ]
    
    def wrap_handle_func_fn(method):
        def handle_func(handler):
            if handler.dispatcher:
                request = ServiceRequest(handler)
                handler.dispatcher.dispatch(method, request)
                handler.dispatcher.after_complete(request)

        return handle_func
    
    handler = DynClassFactory.create(handler_class, {
        'dispatcher': dispatcher
    })

    for method in methods:
        setattr(handler, 'do_'+method, wrap_handle_func_fn(method))

    return handler
