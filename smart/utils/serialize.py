import json, io

from .json import ObjJSONEncoder


class TypeObjSerializer:
    @staticmethod
    def __cast_to_bytes(data):
        if data is None:
            return None

        if not isinstance(data, bytes):
            if not isinstance(data, str):
                data = str(data)

            data = data.encode('utf8')
    
        return data

    @staticmethod
    def encode(obj, obj_type:str=None, str_fn:callable=None)->bytes:
        """序列化 (obj, type)
        
        Arguments:
            obj {any} -- 数据
        
        Keyword Arguments:
            obj_type {str} -- 数据类型 (default: {None})
            str_fn {callable} -- 对象转字符串函数, 缺省使用 json.dumps (default: {None})
        
        Returns:
            bytes -- 数据结构: chr(0) + chr(type_len) + type + obj_str
        """
        if obj is not None:
            if str_fn is None:
                obj_data = json.dumps(obj, ensure_ascii=False, cls=ObjJSONEncoder)
            else:
                obj_data = str_fn(obj)
            obj_data = TypeObjSerializer.__cast_to_bytes(obj_data)
        else:
            obj_data = None

        obj_type = TypeObjSerializer.__cast_to_bytes(obj_type)

        data = io.BytesIO()
        main_ver_data = bytes([0])

        if obj_type is not None:
            data.write(main_ver_data)

            len_type = len(obj_type)
            assert len_type < 256
            data.write(bytes([len_type]))

            if len_type:
                data.write(obj_type)
        
        if obj_data is not None:
            data.write(obj_data)

        return data.getvalue()

    @staticmethod
    def decode(data:bytes, cast_fn:callable=None)->tuple:
        """反序列化type_obj

        type_obj序列化数据结构: main_ver_len(int8), main_ver(int8), type_len(int8), type_str, body_str

        反序列化版本处理逻辑:
        1. main_ver_len > 1, 表示非type_obj协议, body_offset = 0, 兼容纯obj序列化字符串的反序列化
        2. main_ver_len = 0, 表示 main_ver为None, 因此无sub_ver, type_len_offset = 1
        3. main_ver_len = 1, 表示有 main_ver, 将抛出NotImplementedError异常, 为以后版本扩展预留
        
        Arguments:
            data {bytes} -- 序列化的数据
        
        Keyword Arguments:
            cast_fn {callable} -- 字符串转obj函数, 缺省使用 json.loads (default: {None})
        
        Returns:
            tuple -- type, obj
        """
        if not data:
            return None, None
        
        data = TypeObjSerializer.__cast_to_bytes(data)
        
        main_ver_len = data[0]

        if main_ver_len > 1:
            # 兼容纯 json_encode 序列化的数据
            main_ver = None
            type_len_offset = body_offset = 0
        elif main_ver_len == 1:
            main_ver = data[1]
            type_len_offset = 2
        else: 
            main_ver = 0
            type_len_offset = 1
        
        if main_ver and main_ver > 0:
            raise NotImplementedError('TypeObjSerializer ver'+str(main_ver)+' is not implemented')

        if type_len_offset > 0:
            type_len = data[type_len_offset]
            type_offset = type_len_offset + 1
            body_offset = type_offset + type_len
            type = data[type_offset:body_offset].decode('utf8')
        else:
            type = None

        body = data[body_offset:].decode('utf8')

        if cast_fn:
            obj = cast_fn(body)
        else:
            if len(body):
                obj = json.loads(body)
            else:
                obj = None
        
        return type, obj

        