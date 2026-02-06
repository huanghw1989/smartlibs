import typing


def iter_list_or_dict(list_or_dict:typing.Union[dict, list, set, tuple], list_as_val=False, list_as_key=False):
    if not list_or_dict: yield from []

    if isinstance(list_or_dict, (list, set, tuple)):

        for item in list_or_dict:
            if list_as_val:
                yield None, item
            elif list_as_key:
                yield item, None
            else:
                yield item
    elif isinstance(list_or_dict, dict):
        
        for key, val in list_or_dict.items():
            yield key, val

def iter_add(*iter_list):
    for _iter in iter_list:
        yield from _iter