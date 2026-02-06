from smart.rest.base import ExceptionInfo
from smart.rest.base_req import BaseRequest
from smart.rest.__logger import logger_rest



class RstHandlers:    
    @staticmethod
    def no_body(request:BaseRequest, rst):
        pass


class ErrHandlers:
    Default_Opts = {
        'header_code':'APP-ERROR-CODE',
        'header_msg': 'APP-ERROR-MSG'
    }

    def __init__(self, opts=None) -> None:
        self._opts = opts or {}

    def get_opt(self, key):
        val = self._opts.get(key)
        if val is None:
            val = self.Default_Opts.get(key)
        return val

    def header_mode(self, request:BaseRequest, e:BaseException):
        logger_rest.exception(e)
        exception_info = ExceptionInfo.parse(e)
        headers = {}
        headers[self.get_opt('header_code')] = str(exception_info.code)
        headers[self.get_opt('header_msg')] = str(exception_info.msg)
        http_status = exception_info.http_status or 500
        request.response_content(None, http_status=http_status, headers=headers)