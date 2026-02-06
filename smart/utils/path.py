import pathlib, os


def path_part_iter(file_path:str):
    if not file_path:
        return

    split_chars = set(('/', os.sep))
    pos = 0
    n = len(file_path)

    for i in range(0, n):
        if file_path[i] in split_chars:
            yield file_path[pos:i], i
            pos = i + 1
    
    yield file_path[pos:n], n


def path_resolve(file_path:str, context_dir = None, context_file = None):
    if not file_path or (not file_path.startswith('.')):
        return file_path
    
    ctx_path = None

    if context_dir is not None:
        ctx_path = pathlib.PurePath(context_dir)
    elif context_file is not None:
        ctx_path = pathlib.PurePath(context_file).parent
    else:
        return None
    
    for part, pos in path_part_iter(file_path):
        if part == '.':

            continue
        elif part == '..':

            parent_ctx_path = ctx_path.parent

            if parent_ctx_path == ctx_path:
                # 相对路径层数 超出 context文件层数
                return None
            else:
                ctx_path = parent_ctx_path
        elif not part:

            continue
        else:

            ctx_path = ctx_path.joinpath(part)
    
    return str(ctx_path)


def path_join(*paths, auto_mkdir=False):
    """文件路径连接
    
    Keyword Arguments:
        auto_mkdir {bool} -- 自动创建上级目录 (default: {False})
    
    Returns:
        str -- 文件路径
    """
    paths = [path for path in paths if path]
    
    if not paths:
        return ''

    joined_path = os.path.join(*paths)

    if auto_mkdir:
        dir_path = os.path.dirname(joined_path)
        os.makedirs(dir_path, exist_ok=True)
        
    return joined_path


def url_path_join(*paths):
    """url路径拼接

    用法示例:
      url_path_join('1/2/', '3/', '/4', '5') == '1/2/3/4/5'

    Returns:
        str: 拼接后的地址
    """
    paths = [path for path in paths if path]
    if not paths:
        return ''
    _final_path = paths[0]
    for i in range(1, len(paths)):
        _to_concat_path = paths[i]
        if _final_path[-1] == '/':
            if _to_concat_path[0] == '/':
                _final_path += _to_concat_path[1:]
            else:
                _final_path += _to_concat_path
        else:
            if _to_concat_path[0] == '/':
                _final_path += _to_concat_path
            else:
                _final_path += '/' + _to_concat_path
    return _final_path