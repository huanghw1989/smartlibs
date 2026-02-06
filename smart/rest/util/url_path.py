

def url_path_match(to_match_pathes, pattern_pathes, rst_dict=None):
    if not to_match_pathes:
        if not pattern_pathes:
            return rst_dict if rst_dict else True
        else:
            return False

    if not pattern_pathes:
        return False
    
    if len(pattern_pathes) != len(to_match_pathes):
        if '**' not in pattern_pathes:
            return False

    for i, sub_pattern_path in enumerate(pattern_pathes):
        if sub_pattern_path == '**':

            sub_pattern_pathes = pattern_pathes[i+1:]

            for j in range(0, len(to_match_pathes)):
                match_rst = url_path_match(to_match_pathes[j+1:], sub_pattern_pathes, rst_dict=rst_dict)
                if match_rst:
                    return match_rst

            return False
        elif sub_pattern_path == '*':

            return url_path_match(to_match_pathes[i+1:], pattern_pathes[i+1:], rst_dict=rst_dict)
        elif sub_pattern_path.startswith('{') and sub_pattern_path.endswith('}'):
            
            rst_key = sub_pattern_path[1:-1]
            rst_val = to_match_pathes[i]
            rst_dict = rst_dict or {}
            rst_dict[rst_key] = rst_val
            continue

        elif sub_pattern_path == to_match_pathes[i]:

            continue
        else:
            return False
    
    return rst_dict if rst_dict else True


def is_sub_pattern_path(path:str):
    if not path: 
        return False

    if path in ('*', '**'):
        return True

    if path.startswith('{') and path.endswith('}'):
        return True
    
    return False


def split_pathes_to_fix_and_pattern(pathes):
    for i, sub_path in enumerate(pathes):
        if is_sub_pattern_path(sub_path):
            return pathes[:i], pathes[i:]
    
    return pathes, None