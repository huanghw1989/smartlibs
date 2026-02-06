

def cast_bool(val):
    return False if (not val) or (val in ('False', 'false', '0')) else True


def cast_float(val):
    return float(val) if val not in ('', None) else None


def cast_int(val):
    return int(float(val)) if val not in ('', None) else None


def cast_val(type, val):
    if type == 'int':
        return cast_int(val)
    elif type == 'float':
        return cast_float(val)
    elif type == 'str':
        return str(val)
    elif type in ('bool', 'boolean'):
        return cast_bool(val)
    else:
        return val