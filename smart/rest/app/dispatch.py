import threading
from smart.utils.func import func_safe_call
from smart.utils.loader import get_import_path

from smart.rest.base import ExceptionInfo, ResponseKey
from smart.rest.base_req import BaseRequest
from smart.rest.__logger import logger_rest

from .route_manage import RouteHookManage, RouterHandlerFullMeta
from .boot import Bootable


class ServiceDispatcher(Bootable):
    def __init__(self, app:Bootable=None, **kwargs):
        self.__cache_store = None
        self.__error_handler = None
        self.__app:Bootable = app
        self._other_kwargs = kwargs
        if app:
            self.boot_config = app.boot_config
    
    @property
    def _cache_store(self):
        if self.__cache_store is None:
            self.__cache_store = threading.local()
        return self.__cache_store
    
    def _get_cache(self, name):
        _cache_store = self._cache_store
        val = getattr(_cache_store, name, None)
        if val is None:
            val = {}
            setattr(_cache_store, name, val)
        return val
    
    def get_service_instance(self, service_class):
        _cache_instances = self._get_cache("service_instances")
        if service_class not in _cache_instances:
            _cache_instances[service_class] = service_instance = service_class()
            service_instance.app = self.__app

        service_instance = _cache_instances[service_class]

        return service_instance
    
    def set_error_handler(self, error_handler:callable):
        self.__error_handler = error_handler
    
    def handle_error(self, request:BaseRequest, e:BaseException, err_handler=None):
        exception_info = ExceptionInfo.parse(e)

        _err_handler = err_handler or self.__error_handler

        if _err_handler:

            _err_handler(request, exception_info)
        else:

            logger_rest.exception(e)

            return_obj = {}
            return_obj[ResponseKey.code] = exception_info.code
            return_obj[ResponseKey.msg] = exception_info.msg
            http_status = exception_info.http_status or 500

            request.response_json(return_obj, http_status=http_status)
    
    @staticmethod
    def rest_handler(request:BaseRequest, rst):
        if not request.is_responsed:
            request.response_json(rst, wrap_code=True)
            
    def dispatch(self, http_method, request:BaseRequest):
        # 从 url query 参数解析
        query_dict = request.query_dict

        logger_rest.debug('ServiceDispatcher.dispatch %s %s %s', http_method, request.path, query_dict)

        matches = self.boot_config.route_m.find_handler(request.path, http_method)

        if not matches:
            request.send_error(404, explain='No matched route')
            return

        handler:RouterHandlerFullMeta = None
        handler, service_class, func, match_rst = matches

        if isinstance(match_rst, dict):
            request.path_dict = match_rst
        
        # 从 url 路径参数解析
        path_dict = request.path_dict

        service_instance = self.get_service_instance(service_class)
        service_instance.request = request
        service_path = get_import_path(service_instance)
        request._handler = (service_instance, func)

        try:
            before_action_rst = self.exec_hook(request, service_instance, 'before_action', service_path=service_path)
            if before_action_rst:
                action_kwargs = {
                    **query_dict,
                    **path_dict
                }
                rst = func_safe_call(func, [service_instance], action_kwargs)
                request._handle_result = rst
            self.exec_hook(request, service_instance, 'after_action', service_path=service_path)
        except BaseException as e:
            err_handler = handler.route_handler.opts.get('err_handler')
            self.handle_error(request, e, err_handler=err_handler)
        else:
            rst_handler = handler.route_handler.opts.get('rst_handler') or self.rest_handler
            rst = request._handle_result
            rst_handler(request, rst)
        # service_instance.request = None
    
    def exec_hook(self, request, service_instance, stage, service_path=None):
        if not service_path:
            service_path =  get_import_path(service_instance)
        before_action_list = RouteHookManage.get_hook_list(service_path, stage)
        req_path = request.path
        for before_action in before_action_list:
            hook_rst = before_action(service_instance)
            if hook_rst is False:
                logger_rest.debug('ServiceDispatcher.exec_hook %s %s early_stop by %s', stage, req_path, before_action)
                return False
        return True
    
    def after_complete(self, request:BaseRequest):
        service_instance, func = request._handler or (None, None)
        if service_instance:
            try:
                self.exec_hook(request, service_instance, 'after_complete')
            except BaseException as e:
                logger_rest.warning("ServiceDispatcher.after_complete error %s %s", request.path, e)
