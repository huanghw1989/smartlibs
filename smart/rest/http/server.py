from http.server import HTTPServer

from .handler import wrap_request_handler
from ..app.base_app import BaseApplication, BaseAppServer
from .dispatch import RestHttpDispatcher
from ..__logger import logger_rest


class RestHttpServer(BaseAppServer):
    DEFAULT_HOST = ''
    DEFAULT_PORT = 80

    def __init__(self, port=None, host=None, http_server=None, **kwargs) -> None:
        self._httpd = None
        self.port = port
        self.host = host
        if http_server is None:
            try:
                from http.server import ThreadingHTTPServer
                http_server = ThreadingHTTPServer
            except:
                # 兼容python 3.6
                from .ThreadingHTTPServer import ThreadingHTTPServer
                http_server = ThreadingHTTPServer
        self._http_server_class = http_server
        logger_rest.debug("RestHttpServer use %s", http_server)

    def start(self, app:BaseApplication):
        server_address = (self.host or self.DEFAULT_HOST, self.port or self.DEFAULT_PORT)
        self.dispatcher = RestHttpDispatcher(app)
        self.request_hanlder = wrap_request_handler(
            dispatcher=self.dispatcher
        )
        self._httpd:HTTPServer = self._http_server_class(server_address, self.request_hanlder)

    def daemon(self):
        if self._httpd is None:
            raise Exception("RestHttpServer.daemon failed, should call RestHttpServer.start first")
        self._httpd.serve_forever()

    def close(self):
        if self._httpd:
            self._httpd.server_close()