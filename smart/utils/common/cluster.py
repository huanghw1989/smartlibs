from smart.utils.number import safe_parse_int


def parse_nodes_host(nodes, default_port:int=80, split_char=','):
    """解析节点域名端口
    Use Example: 
        parse_nodes_host('node0,node1:82', 81) => [(node0, 81), (node1, 82)]
        parse_nodes_host(['node0', ('node1', 82), 'node2:83'], 81) => [('node0', 81), ('node1', 82), ('node2', 83)]

    Args:
        nodes (str|list): 域名端口, 多节点用split_char分割
        default_port (int, optional): 缺省端口. Defaults to 80.
        split_char (str, optional): 多节点分割字符. Defaults to ','.

    Returns:
        _type_: _description_
    """
    if not nodes:
        return []
    host_port_list = []
    val_list = nodes.split(split_char) if not isinstance(nodes, (tuple, list)) else nodes
    for val in val_list:
        if not val:
            continue
        host, *info = val.rsplit(':', 1) if not isinstance(val, (tuple, list)) else val
        port = safe_parse_int(info[0], default_port) if info else default_port
        host_port_list.append((host, port))
    return host_port_list