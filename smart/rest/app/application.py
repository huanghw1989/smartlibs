from .base_app import BaseApplication, BaseAppServer

from ..http.server import RestHttpServer
from ..wsgi.server import RestWsgiServer

from ..__logger import logger_rest


class RestServiceApplication(BaseApplication):
    def __init__(self, server_class=None, **kwargs):
        super().__init__(**kwargs)

        self.httpd:BaseAppServer = None
        self.server_class = server_class
        self._server_kwargs = kwargs

        self._status = None
    
    def start(self, wsgi_mode=False):
        self._status = 'start'

        boot_config = self.boot_config

        if boot_config == None:
            logger_rest.error('miss boot config')
        
        boot_config.init()

        if boot_config.opts.crond_enable:
            self.start_crond()
        
        return self.__start_httpd(wsgi_mode=wsgi_mode)
    
    def __start_httpd(self, wsgi_mode=False):
        server_class = self.server_class
        if server_class is None:
            server_class = RestWsgiServer if wsgi_mode else RestHttpServer

        self.httpd = httpd = server_class(**self._server_kwargs)
        httpd.start(app=self)

        app_class = type(self).__name__
        svr_class = server_class.__name__
        port = self._server_kwargs.get("port")

        logger_rest.info('%s.start %s%s...', app_class, svr_class, 
            '(port={})'.format(str(port)) if port else '')

        return httpd
    
    def daemon(self):
        httpd = self.httpd

        try:
            if httpd is None:
                httpd = self.start(wsgi_mode=False)
            httpd.daemon()
        except KeyboardInterrupt:

            logger_rest.info('End RestServiceApplication (KeyboardInterrupt)')
        else:

            logger_rest.info('End RestServiceApplication')
        finally:

            if httpd:
                httpd.close()
                
            self.close(close_once=True)
    
    def wsgi(self, env, start_response):
        httpd:RestWsgiServer = self.httpd
        resp = httpd.wsgi(env=env, start_response=start_response)
        return resp
        
    def shutdown(self):
        if self.httpd is not None:
            self.httpd.shutdown()

        self.close(close_once=True)
    
    def close(self, close_once=False):
        if close_once and self._status == 'close':
            # has closed
            return

        logger_rest.debug('close RestServiceApplication')
        self._status = 'close'
        self.end_crond()
