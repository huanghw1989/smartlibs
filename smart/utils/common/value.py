
def is_null(val):
    return val is None

def is_not_null(val):
    return val is not None

def alway_true(val):
    return True

def alway_false(val):
    return False

def if_null(val, null_val):
    return val if val is not None else null_val