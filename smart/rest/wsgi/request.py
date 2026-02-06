import io, inspect
from collections import OrderedDict
from urllib.parse import parse_qs

from http.client import HTTPMessage
from http.server import BaseHTTPRequestHandler
from smart.utils.number import safe_parse_int

from ..base_req import BaseRequest
from ..__logger import logger_rest


class HttpHeaderKey:
    content_type = 'Content-Type'
    status_code = 'Status Code'

class HttpHeaders:
    content_json = (HttpHeaderKey.content_type, 'application/json')
    

class RestWsgiRequest(BaseRequest):
    """Wsgi请求
    Wsgi协议: https://peps.python.org/pep-0333/#input-and-error-streams
    """
    def __init__(self, env:dict, start_response):
        super().__init__()
        self._env = env
        self._start_response = start_response

        self.__full_path:str = env.get('REQUEST_URI')
        self.__path:str = env.get('PATH_INFO')
        self.__query_str:str = env.get('QUERY_STRING')
        self.__client_address:tuple = (env.get('REMOTE_ADDR'), safe_parse_int(env.get('REMOTE_PORT')))
        
        self.command = env.get('REQUEST_METHOD')
        self.close_connection = False
        self.headers:HTTPMessage = HTTPMessage()
        for k, v in env.items():
            if k.startswith('HTTP_'):
                self.headers[k[5:].replace('_', '-')] = v
            elif k in ('CONTENT_LENGTH', 'CONTENT_TYPE'):
                self.headers[k.replace('_', '-')] = v
        # self.headers['Content-Length']
        # self.headers['Content-Type']
        self.protocol_version = env.get('SERVER_PROTOCOL') # HTTP/1.1
        self.requestline = '{} {} {}'.format(self.command, self.__full_path, self.protocol_version) # 'PUT /plan HTTP/1.1'
        self._req_stream:io.IOBase = env.get('wsgi.input')
        self.__query_dict = None
        self._handle_result = None
        self._resp_headers = OrderedDict()
        self._resp_body = None
        self._resp_code_msg_map = BaseHTTPRequestHandler.responses
        self._resp_status = None
    
    @property
    def client_address(self):
        return self.__client_address

    @property
    def content_length(self):
        len = self.headers['content-length']
        return safe_parse_int(len) if len is not None else len

    @property
    def input_stream(self) -> io.IOBase:
        return self._req_stream
    
    @property
    def path(self):
        return self.__path

    @property
    def full_path(self):
        return self.__full_path
    
    @property
    def query_dict(self):
        if self.__query_dict is None:
            self.__query_dict = {
                k: v[0] if len(v) == 1 else v
                for k, v in parse_qs(self.__query_str).items()
            }

        return self.__query_dict
    
    def _set_resp_status(self, code, message=None):
        if message is None:
            if code in self._resp_code_msg_map:
                message = self._resp_code_msg_map[code][0]
            else:
                message = ''
        self._resp_status = str(code) + ' ' + message
    
    def send_error(self, code, message=None, explain=None):
        logger_rest.error("RestWsgiRequest.send_error %s %s %s", code, message, explain)
        self.response_json(obj={}, wrap_code=True, 
            http_status=code, 
            headers={'Connection': 'close'},
            err_code=1,
            err_msg=explain)
    
    def set_resp_header(self, keyword, value):
        self._resp_headers[keyword] = value
    
    def response_content(self, content, http_status=200, headers:dict=None):
        self.is_responsed = True
        self._set_resp_status(http_status)
        content_is_iter = inspect.isgenerator(content)
        if content:
            if isinstance(content, str):
                content = content.encode('utf8')
        
        if not content_is_iter:
            self.set_resp_header('Content-Length', str(len(content) if content else 0))

        if headers:
            self._resp_headers.update(headers)
        
        if content:
            self._resp_body = content
    
    def json_param(self, key, defaultVal=None):
        return self.json_body.get(key, defaultVal)

    def wsgi_status(self):
        return self._resp_status or '200 OK'

    def wsgi_headers(self):
        return [(k, v) for k, v in (self._resp_headers or {}).items()]
    
    def wsgi_body(self, after_complete:callable=None):
        _body = self._resp_body
        try:
            if _body is None:
                return
            
            if isinstance(_body, bytes):
                yield _body
            elif inspect.isgenerator(_body):
                for _data in _body:
                    yield _data
        finally:
            if after_complete:
                after_complete(self)