import  inspect

from .route_manage import BaseRoute, RouteHandlerMeta, RouteManage, RouteHookManage

from ..__logger import logger_rest


class RestRoute(BaseRoute):
    def __init__(self):
        BaseRoute.__init__(self)
        self.hook = RouteHook()
    
    def service(self, path_prefix:str=None):
        route = self

        def decorator(clazz):
            if inspect.isclass(clazz):
                logger_rest.debug('RestRoute path %s -> %s', path_prefix, clazz)
                RouteManage.add_route_service(clazz, route, path_prefix)

            return clazz

        return decorator

    def request(self, path:str, methods=['GET', 'POST'], rst_handler=None, err_handler=None):
        path = path.lstrip('/')

        def decorator(func):
            logger_rest.debug('RestRoute %s %s -> %s', path, methods, func)

            self.route_handlers.append(RouteHandlerMeta(
                handler = func,
                path = path,
                http_methods = methods,
                rst_handler = rst_handler,
                err_handler = err_handler
            ))
            
            return func

        return decorator
    
    def get(self, path):
        return self.request(path, methods=['GET'])

    def post(self, path):
        return self.request(path, methods=['POST'])

    def put(self, path):
        return self.request(path, methods=['PUT'])

    def delete(self, path):
        return self.request(path, methods=['DELETE'])

    def options(self, path):
        return self.request(path, methods=['OPTIONS'])

    def head(self, path):
        return self.request(path, methods=['HEAD'])


class RouteHook:
    def before_action(self):
        def decorator(func):
            RouteHookManage.add_hook(func, 'before_action')
            return func

        return decorator

    def after_action(self):
        def decorator(func):
            RouteHookManage.add_hook(func, 'after_action')
            return func

        return decorator

    def after_complete(self):
        def decorator(func):
            RouteHookManage.add_hook(func, 'after_complete')
            return func

        return decorator