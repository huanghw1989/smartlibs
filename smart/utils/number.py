

def safe_parse_int(val, default_val=None):
    if val in (None, ''):
        return default_val
        
    try:
        return int(val)
    except Exception:
        return default_val

def safe_parse_float(val, default_val=None):
    if val in (None, ''):
        return default_val
    
    try:
        return float(val)
    except Exception:
        return default_val