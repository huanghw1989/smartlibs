from ..base import ResponseKey


class BaseAsyncRequestHandler:
    def send_error(self, request, code, message=None, explain=None, headers:dict=None):
        data = {}
        data[ResponseKey.code] = 1
        data[ResponseKey.msg] = message

        if explain:
            data['explain'] = explain

        self.send_response(request, data, headers=headers, http_status=code)

    def send_response(self, request, data, headers:dict=None, http_status:int=200, type='json'):
        pass