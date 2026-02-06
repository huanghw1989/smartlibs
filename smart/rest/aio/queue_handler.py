from queue import Queue

from .handler import BaseAsyncRequestHandler

from smart.rest.__logger import logger_rest


class QueueAsyncRequestHandler(BaseAsyncRequestHandler):
    def __init__(self, resp_queue:Queue):
        self.resp_queue = resp_queue

    def send_response(self, request, data, headers:dict=None, http_status:int=200, type='json'):
        resp_data = {
            'status': http_status,
            'type': type,
            'data': data,
            'headers': headers,
            'req_id': getattr(request, 'req_id', None),
            'req_addr': request.client_address,
        }
        # logger_rest.debug('QueueAsyncRequestHandler send: %s', resp_data)
        self.resp_queue.put(resp_data)