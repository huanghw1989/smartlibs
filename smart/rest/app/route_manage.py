from smart.utils.dict import dict_get_or_set, dict_safe_get
from smart.utils.loader import get_func_cls_path

from .module_manage import ModuleManage, ModuleClsType

from ..util import url_path

from ..__logger import logger_rest


class RouteHandlerMeta:
    def __init__(self, handler:callable, path:str, http_methods:list, **kwargs):
        self.handler = handler
        self.path = path
        self.http_methods = http_methods
        self.opts = kwargs


class BaseRoute():
    def __init__(self):
        self.route_handlers = []


class RouterMeta:
    def __init__(self, service_cls, route:BaseRoute, path_prefix:str=None):
        self.service_cls = service_cls
        self.route = route
        self.path_prefix = path_prefix


class RouterHandlerFullMeta:
    def __init__(self, router:RouterMeta, route_handler:RouteHandlerMeta, fix_pathes, pattern_pathes):
        """路由处理器的完整信息

        Args:
            router (RouterMeta): 类路由器, 类装饰器RestRoute.service生成
            route_handler (RouteHandlerMeta): 函数路由处理器
            fix_pathes (_type_): _description_
            pattern_pathes (_type_): _description_
        """
        self.router = router
        self.route_handler = route_handler
        self.fix_pathes = fix_pathes
        self.pattern_pathes = pattern_pathes


class RouteManage:
    """路由管理

    每个应用启动器实例初始化一个模块管理实例(ModuleManage)和一个路由管理实例. 
    """
    # 模块-路由映射表: {module_path: [RouterMeta]}
    # 存储所有路由服务信息
    module_routers_map = {}

    def __init__(self, module_m:ModuleManage):
        """
        Args:
            module_m (ModuleManage): 模块管理实例
        """
        self.module_m = module_m
        self.pathes_handlers_map = {}

    @staticmethod
    def add_route_service(clazz, route:BaseRoute, path_prefix:str=None):
        """添加路由服务类

        RestRoute.service装饰器调用

        Args:
            clazz (class): 被装饰器的类
            route (BaseRoute): 路由实例
            path_prefix (str, optional): 路径前缀. Defaults to None.
        """
        mod_path = ModuleManage.register_class(clazz, ModuleClsType.service)

        if mod_path:
            routers = dict_get_or_set(RouteManage.module_routers_map, (mod_path,), [])
            routers.append(RouterMeta(
                service_cls=clazz,
                route=route,
                path_prefix=path_prefix
            ))

    def init(self):
        """初始化路由处理函数

        处理逻辑:
            应用启动器导入所有需要的模块文件, 依赖模块文件路径由 ModuleManage 实例管理
            模块文件被import时, 将触发RestRoute的装饰器, 调用 RouteManage.add_route_service 保存所有路由信息(RouterMeta)
            应用启动器触发 RouteManage.init, 根据 ModuleManage 实例的模块路径判断 RouterMeta 是否是应用配置的模块, 将信息保存到 pathes_handlers_map 
            当接收到http请求时, 调用 find_handler 查找控制器方法
        """
        for mod_path, mod_obj in self.module_m.all_module.items():
            routers = self.module_routers_map.get(mod_path, [])
            for router in routers:
                router:RouterMeta
                path_prefix = (router.path_prefix or '').split('/')
                for route_handler in router.route.route_handlers:
                    route_handler:RouteHandlerMeta
                    # route_handler.service_cls = router.service_cls

                    pathes = (route_handler.path or '').split('/')
                    pathes = tuple(filter(None, (*path_prefix, *pathes)))
                    fix_pathes, pattern_pathes = url_path.split_pathes_to_fix_and_pattern(pathes)

                    handlers = dict_get_or_set(self.pathes_handlers_map, (fix_pathes,), [])
                    handlers.append(RouterHandlerFullMeta(
                        router = router,
                        route_handler = route_handler,
                        fix_pathes = fix_pathes,
                        pattern_pathes = pattern_pathes
                    )) 
    
    def __match_http_method(self, target_http_method, http_methods):
        if http_methods is None:
            return True
        
        if '*' in http_methods:
            return True
        
        return target_http_method in http_methods
    
    def find_handler(self, path, http_method):
        pathes = tuple(filter(None, 
            (path or '').split('/')
        ))

        for i in range(len(pathes), -1, -1):
            handlers = self.pathes_handlers_map.get(pathes[:i])

            if handlers:
                to_match_pathes = pathes[i:]

                for handler in handlers:
                    handler:RouterHandlerFullMeta
                    match_rst = url_path.url_path_match(to_match_pathes, handler.pattern_pathes)
                    
                    if match_rst not in (False, None):
                        if self.__match_http_method(http_method, handler.route_handler.http_methods):
                            return handler, handler.router.service_cls, handler.route_handler.handler, match_rst


class RouteHookManage:
    service_func_map = {}
    @staticmethod
    def add_hook(func, stage):
        service_path = get_func_cls_path(func)
        if service_path:
            hook_list = dict_get_or_set(RouteHookManage.service_func_map, (service_path, stage), [])
            hook_list.append(func)
    
    @staticmethod
    def get_hook_list(service_path, stage):
        if not service_path:
            return []
        return dict_safe_get(RouteHookManage.service_func_map, (service_path, stage), [])
