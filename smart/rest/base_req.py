from abc import ABC, abstractmethod
import json, io
from .base import ResponseKey


class HttpHeaderKey:
    content_type = 'Content-Type'
    status_code = 'Status Code'


class HttpHeaders:
    content_json = (HttpHeaderKey.content_type, 'application/json')


class BaseRequest(ABC):
    def __init__(self) -> None:
        self.__json_body = None
        self.__path_dict = None
        self._body = None
        self._handler = None # (service_instance, func)
        self.__ctx = {}
        self.is_responsed = False

    @property
    @abstractmethod
    def client_address(self):
        pass

    @property
    @abstractmethod
    def content_length(self):
        return None

    @property
    def input_stream(self) -> io.IOBase:
        return None

    @property
    def output_stream(self):
        return None

    @property
    def body(self):
        if self._body is None:
            input_stream = self.input_stream
            if input_stream is not None:
                content_length = self.content_length
                if content_length:
                    self._body = input_stream.read(content_length)
                elif content_length is None:
                    # miss header content-length
                    self._body = input_stream.read()
                else:
                    # content_length=0
                    self._body = b''
            else:
                self._body = b''
        return self._body

    @property
    def json_body(self):
        if self.__json_body is None:
            self.__json_body = json.loads(self.body.decode('utf8')) if self.body else {}

        return self.__json_body

    @property
    @abstractmethod
    def path(self):
        pass

    @property
    @abstractmethod
    def full_path(self):
        pass

    @property
    @abstractmethod
    def query_dict(self):
        pass

    @property
    def path_dict(self):
        return self.__path_dict if self.__path_dict is not None else {}

    @path_dict.setter
    def path_dict(self, path_dict):
        self.__path_dict = path_dict

    @abstractmethod
    def send_error(self, code, message=None, explain=None):
        pass

    @abstractmethod
    def set_resp_header(self, keyword:str, value:str):
        pass

    @abstractmethod
    def response_content(self, content, http_status=200, headers:dict=None):
        """发送响应

        Args:
            content (bytes|str|generator): 响应的内容
            http_status (int, optional): http状态码. Defaults to 200.
            headers (dict, optional): 响应头. Defaults to None.
        """
        pass

    def response_json(self, obj, wrap_code=False, http_status=200, headers:dict=None, err_code=None, err_msg=None):
        """发送json格式的响应数据

        Args:
            obj (any): 可json序列化的对象, 响应的内容
            wrap_code (bool, optional): 是否外层嵌套code. Defaults to False.
            http_status (int, optional): http状态码. Defaults to 200.
            headers (dict, optional): 响应头. Defaults to None.
            err_code (int, optional): 应用错误码, 仅当wrap_code有效. Defaults to None.
            err_msg (str, optional): 应用错误消息, 仅当wrap_code有效. Defaults to None.
        """
        if wrap_code:
            wrap_obj = {}
            wrap_obj[ResponseKey.code] = err_code or 0
            if err_msg is not None:
                wrap_obj[ResponseKey.msg] = err_msg
            wrap_obj[ResponseKey.data] = obj
            obj = wrap_obj

        resp_body = json.dumps(obj, ensure_ascii=False).encode('utf8')
        _headers = dict((HttpHeaders.content_json, ))
        if headers:
            _headers.update(headers)

        self.response_content(resp_body, http_status=http_status, headers=_headers)

    @abstractmethod
    def json_param(self, key, defaultVal=None):
        pass

    def get_param(self, key, defaultVal=None):
        val = self.path_dict.get(key)

        if val is None:
            val = self.query_dict.get(key)
        
        if val is None:
            val = self.json_param(key, defaultVal=defaultVal)
        
        return val if val is not None else defaultVal
    
    @property
    def context(self):
        return self.__ctx