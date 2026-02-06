# import yaml as _yaml
from yaml import load, dump
from io import StringIO


try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    
    from yaml import Loader, Dumper


def yaml_load(stream):
    return load(stream, Loader=Loader)


def yaml_load_file(file, encoding='utf8'):
    with open(file, 'r', encoding=encoding) as f:
        return yaml_load(f)


def yaml_dump(data, stream, **kwargs):
    if 'sort_keys' not in kwargs:
        kwargs['sort_keys'] = False
    
    if 'allow_unicode' not in kwargs:
        kwargs['allow_unicode'] = True

    return dump(data, stream, Dumper=Dumper, **kwargs)


def yaml_dumps(data, **kwargs):
    stream = StringIO()
    yaml_dump(data, stream, **kwargs)

    return stream.getvalue()


# from collections import OrderedDict

# def ordered_load(stream, Loader=Loader, object_pairs_hook=OrderedDict):
#     class OrderedLoader(Loader):
#         pass
#     def construct_mapping(loader, node):
#         loader.flatten_mapping(node)
#         return object_pairs_hook(loader.construct_pairs(node))
#     OrderedLoader.add_constructor(
#         _yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
#         construct_mapping)
#     return load(stream, OrderedLoader)

# def ordered_dump(data, stream=None, Dumper=Dumper, **kwds):
#     class OrderedDumper(Dumper):
#         pass
#     def _dict_representer(dumper, data):
#         return dumper.represent_mapping(
#             _yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
#             data.items())
#     OrderedDumper.add_representer(OrderedDict, _dict_representer)
#     return dump(data, stream, OrderedDumper, **kwds)