import inspect, threading
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler
from http.client import HTTPMessage
from urllib.parse import urlparse, parse_qs
from ..base_req import BaseRequest
from ..__logger import logger_rest


class HttpHeaderKey:
    content_type = 'Content-Type'
    status_code = 'Status Code'

class HttpHeaders:
    content_json = (HttpHeaderKey.content_type, 'application/json')
    

class ServiceRequest(BaseRequest):
    def __init__(self, request:BaseHTTPRequestHandler):
        super().__init__()
        self._request = request

        self.__full_path = request.path
        self.__client_address:tuple = request.client_address
        
        self.command = request.command
        self.close_connection:bool = request.close_connection
        self.headers:HTTPMessage = request.headers
        self.protocol_version = request.protocol_version
        self.requestline = request.requestline
        
        self.__query_dict = None
        self.__path = None
        self.__resp_headers = OrderedDict()
        self._handle_result = None
    
    @property
    def client_address(self):
        return self.__client_address

    @property
    def content_length(self):
        return int(self._request.headers['content-length'] or 0)

    @property
    def input_stream(self):
        return self._request.rfile

    @property
    def output_stream(self):
        return self._request.wfile
    
    def __parse_full_path(self):
        path_info = urlparse(self.full_path)
        self.__path = path_info.path
        self.__query_dict = {
            k: v[0] if len(v) == 1 else v
            for k, v in parse_qs(path_info.query).items()
        }
    
    @property
    def path(self):
        if self.__path is None:
            self.__parse_full_path()

        return self.__path

    @property
    def full_path(self):
        return self.__full_path
    
    @property
    def query_dict(self):
        if self.__query_dict is None:
            self.__parse_full_path()

        return self.__query_dict

    def _get_lock(self, name):
        _key = ('lock', name)
        lock = self.context.get(_key)
        if lock is None:
            self.context[_key] = lock = threading.Lock()
        return lock
    
    def _call_with_lock(self, cb, lock_name, timeout=1):
        lock = self._get_lock(lock_name)
        try:
            got = lock.acquire(timeout=timeout)
            if not got:
                logger_rest.warning("http.ServiceRequest failed acquire lock %s", lock_name)
            # else:
            #     logger_rest.debug("http.ServiceRequest acquired lock %s", lock_name)
            return cb()
        finally:
            try:
                lock.release()
                # logger_rest.debug("http.ServiceRequest released lock %s", lock_name)
            except:
                logger_rest.debug("http.ServiceRequest failed release lock %s", lock_name)
    
    def send_error(self, code, message=None, explain=None):
        logger_rest.error("ServiceRequest.send_error %s %s %s", code, message, explain)
        self.response_json(obj={}, wrap_code=True, http_status=code, err_code=1, err_msg=explain)
        # self._call_with_lock(
        #     lambda :self._request.send_error(code, message=message, explain=explain),
        #     'wfile')
    
    def set_resp_header(self, keyword, value):
        self.__resp_headers[keyword] = value

    def response_content(self, content, http_status=200, headers=None):
        self.is_responsed = True
        send_header = self._request.send_header
        self._request.send_response(http_status)
        content_is_iter = inspect.isgenerator(content)
        if content:
            if isinstance(content, str):
                content = content.encode('utf8')
        
        if not content_is_iter:
            send_header('Content-Length', str(len(content) if content else 0))

        if headers:
            self.__resp_headers.update(headers)
        for header_key, header_val in self.__resp_headers.items():
            send_header(header_key, header_val)
        
        self._request.end_headers()
        if content_is_iter:
            for _sub_content in content:
                self._call_with_lock(
                    lambda :self._request.wfile.write(_sub_content),
                    'wfile')
        elif content:
            self._call_with_lock(
                lambda :self._request.wfile.write(content),
                'wfile')
    
    def json_param(self, key, defaultVal=None):
        return self.json_body.get(key, defaultVal)