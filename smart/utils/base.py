

class ApiException(Exception):
    def __init__(self, msg, code):
        self.code = code
        self.msg = msg
        Exception.__init__(self, msg, code)