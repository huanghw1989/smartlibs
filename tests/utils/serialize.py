from smart.utils.serialize import *


def test_type_obj():
    obj_type_list = [
        ({'a': 1, 'b': '啊'}, None),
        ({'x', 'y'}, 'set'),
        ((1, 2), 'tuple'),
        (1.2e5, 'float'),
        (['xxx'], ''),
        (None, 'none'),
        (None, None),
    ]

    for obj_type in obj_type_list:
        obj, type = obj_type
        print('raw: ', (type, obj))

        data = TypeObjSerializer.encode(obj, type)

        len_type = data[0] if data else None
        print('encode: ', (len_type, data.decode('utf8')))

        d_type, d_obj = TypeObjSerializer.decode(data)
        print('decode: ', (d_type, d_obj))

        if obj:
            obj_json_str = json.dumps(obj, ensure_ascii=False, cls=ObjJSONEncoder)
            print('json_encode: ', obj_json_str)
            d_type, d_obj = TypeObjSerializer.decode(obj_json_str)
            print('decode pure json: ', (d_type, d_obj))
            
        print('')



if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)