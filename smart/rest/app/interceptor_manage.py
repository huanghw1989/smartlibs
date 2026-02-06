from ..http.request import ServiceRequest

from .interceptor import BaseInterceptor

# TODO
class InterceptorManage:
    def __init__(self):
        self.__interceptors = []

    def add_interceptor(self, interceptor, priority=None):
        priority = priority or 10
        self.__interceptors.append((interceptor, priority))
        
    def pre_handle(self, request:ServiceRequest) -> bool:
        return True

    def after_handle(self, request:ServiceRequest):
        pass

    def after_complete(self, request:ServiceRequest):
        pass