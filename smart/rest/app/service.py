from ..http.request import ServiceRequest
from .boot import Bootable


class RestService:
    def __init__(self, **kwargs):
        self.request:ServiceRequest = None
        self.app:Bootable = None
    
    def json_param(self, key, defaultVal=None):
        return self.request.json_param(key, defaultVal) if self.request else defaultVal