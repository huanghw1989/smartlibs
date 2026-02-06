

def iter_fixed_len(list_or_tuple, fix_len:int, pad_val=None, left_pad=False):
    assert fix_len >= 1

    if left_pad:
        if not isinstance(list_or_tuple, list):
            list_or_tuple = list(list_or_tuple)
        pad_len = fix_len - len(list_or_tuple)

        for i in range(pad_len):
            yield pad_val
    i = 0

    for item in list_or_tuple:
        yield item
        i += 1
        
        if i >= fix_len:
            break

    if not left_pad:
        for _ in range(i, fix_len):
            yield pad_val


def tuple_fixed_len(list_or_tuple, fix_len:int, pad_val=None, left_pad=False):
    if len(list_or_tuple) == fix_len:
        return list_or_tuple

    return tuple(iter_fixed_len(list_or_tuple, fix_len, pad_val=pad_val, left_pad=left_pad))