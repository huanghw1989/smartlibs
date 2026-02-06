from json import JSONEncoder


class JsonVal:
    def __init__(self, val):
        self.val = val


class BaseJSONEncoder(JSONEncoder):
    NoneVal = JsonVal(None)

    def handle(self, obj):
        pass

    def default(self, obj):
        rst = self.handle(obj)

        if isinstance(rst, JsonVal):

            return rst.val
        elif isinstance(rst, set):

            return list(rst)
        elif rst is not None:
            
            return rst
            
        return JSONEncoder.default(self, obj)
    
    def __call__(self, *args, **kwargs):
        return self


class ObjJSONEncoder(BaseJSONEncoder):
    def handle(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
            
        return str(obj)