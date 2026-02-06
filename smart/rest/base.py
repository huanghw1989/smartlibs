

class RequestException(BaseException):
    def __init__(self, msg='', code=1, http_status=500, *args):
        super().__init__(msg, code, http_status, *args)
        self.msg = msg
        self.code = code
        self.http_status = http_status


class ExceptionInfo():
    DEFAULT_ERR_CODE = 1
    DEFAULT_ERR_HTTP_STATUS = 500
    DEFAULT_ERR_MSG = ''

    def __init__(self, **kwargs):
        self.msg = kwargs.pop('msg', self.DEFAULT_ERR_MSG)
        self.code = kwargs.pop('code', self.DEFAULT_ERR_CODE)
        self.http_status = kwargs.pop('http_status', self.DEFAULT_ERR_HTTP_STATUS)
        self.exception:BaseException = kwargs.pop('exception', None)
        self.other_info = kwargs
    
    @staticmethod
    def parse(e:BaseException):
        msg = getattr(e, 'msg') if hasattr(e, 'msg') else e.__class__.__name__ + str(e.args)
        code = getattr(e, 'code') if hasattr(e, 'code') else ExceptionInfo.DEFAULT_ERR_CODE
        http_status = getattr(e, 'http_status') if hasattr(e, 'http_status') else ExceptionInfo.DEFAULT_ERR_HTTP_STATUS
        return ExceptionInfo(
            msg = msg,
            code = code,
            http_status = http_status,
            exception = e
        )


class ResponseKey:
    code = 'code'
    data = 'data'
    msg = 'msg'