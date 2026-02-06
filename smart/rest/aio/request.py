import json

from urllib.parse import urlencode

from smart.utils.json import ObjJSONEncoder

from ..base import ResponseKey
from ..base_req import BaseRequest
from .handler import BaseAsyncRequestHandler


class AsyncReqData:
    def __init__(self, req_id=None, addr=None, command=None, ver=None, path=None, 
            headers=None, query=None, data=None, **kwargs):
        
        self.req_id:str = req_id # 请求ID
        self.addr = addr # 客户端地址, (ip, port)
        self.command:str = command # GET/POST/PUT/...
        self.ver:str = ver # 协议版本
        self.path:str = path # 请求路径
        self.headers:dict = headers
        self.query:dict = query
        self.data:dict = data
        self._d:dict = kwargs
    
    def to_dict(self):
        data = self.__dict__.copy()
        opts = data.pop('_d', None) or {}
        data.update(opts)
        
        return data


class AsyncRequest(BaseRequest):
    def __init__(self, req_data:AsyncReqData, handler:BaseAsyncRequestHandler):
        self._req_data = req_data
        self.req_id = req_data.req_id

        self.__client_address = req_data.addr or ('', 0)
        self.command = req_data.command or 'GET'
        self.close_connection:bool = False
        self.headers:dict = req_data.headers
        self.protocol_version = req_data.ver or '0.1'

        self.__query_dict = req_data.query or {}
        self.__path = req_data.path or ''
        self.__json_body = req_data.data or {}
        
        self.__path_dict = None
        self.__full_path = None
        self.__body = None
        self._handle_result = None

        self.is_responsed = False
        self._send_headers = {}
        self._handler = handler

    @property
    def client_address(self):
        return self.__client_address

    @property
    def content_length(self):
        return int(self.headers.get('content-length', 0))
    
    @property
    def body(self):
        if self.__body is None:
            self.__body = json.dumps(self.__json_body, ensure_ascii=False, cls=ObjJSONEncoder)

        return self.__body

    @property
    def json_body(self):
        return self.__json_body

    @property
    def path(self):
        return self.__path
    
    @property
    def full_path(self):
        if self.__full_path is None:
            self.__full_path = self.path
            
            if self.query_dict:
                self.__full_path += '?' + urlencode(self.query_dict)

        return self.__full_path
    
    @property
    def requestline(self):
        return '{} {} ASYNC/{}'.format(
            self.command,
            self.full_path,
            self.protocol_version,
        )

    @property
    def query_dict(self):
        return self.__query_dict

    @property
    def path_dict(self):
        return self.__path_dict if self.__path_dict is not None else {}

    @path_dict.setter
    def path_dict(self, path_dict):
        self.__path_dict = path_dict

    def json_param(self, key, defaultVal=None):
        return self.json_body.get(key, defaultVal)
    
    def get_param(self, key, defaultVal=None):
        val = self.path_dict.get(key)

        if val is None:
            val = self.query_dict.get(key)
        
        if val is None:
            val = self.json_param(key, defaultVal=defaultVal)
        
        return val if val is not None else defaultVal
    
    def send_header(self, keyword, value):
        self._send_headers[keyword] = value
    
    def send_error(self, code, message=None, explain=None):
        self._handler.send_error(self, code, message=message, explain=explain, headers=self._send_headers)
        self.is_responsed = True
    
    def response_content(self, content, http_status=200, headers=None):
        if headers:
            self._send_headers.update(headers)

        self._handler.send_response(self, content, headers=self._send_headers, http_status=http_status, type='raw')
        self.is_responsed = True

    def response_json(self, obj, wrap_code=False, http_status:int=200, headers=None):
        if wrap_code:
            wrap_obj = {}
            wrap_obj[ResponseKey.code] = 0
            wrap_obj[ResponseKey.data] = obj
            obj = wrap_obj
        
        if headers:
            self.headers.update(headers)
        
        self._handler.send_response(self, obj, headers=self.headers, http_status=http_status)
        self.is_responsed = True
