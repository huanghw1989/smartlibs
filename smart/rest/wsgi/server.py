from ..app.base_app import BaseApplication, BaseWsgiServer
from .dispatch import RestWsgiDispatcher
from .request import RestWsgiRequest


class RestWsgiServer(BaseWsgiServer):
    def __init__(self, **kwargs) -> None:
        self.dispatcher = None

    def start(self, app:BaseApplication):
        self.dispatcher = RestWsgiDispatcher(app)

    def wsgi(self, env:dict, start_response:callable):
        assert self.dispatcher is not None
        request = RestWsgiRequest(env=env, start_response=start_response)

        http_method = request.command
        self.dispatcher.dispatch(http_method=http_method, request=request)

        status = request.wsgi_status()
        headers = request.wsgi_headers()
        start_response(status, headers)
        resp_body = request.wsgi_body(after_complete=self.dispatcher.after_complete)
        return resp_body

    def close(self):
        pass
