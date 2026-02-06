

def ratio_normalize(ratio:list):
    """比例正则化

    Arguments:
        ratio {list} -- 比例数组

    Returns:
        list -- 总和等于 1
    """
    sum_ratio = sum(ratio)

    return [x/sum_ratio for x in ratio]


def ratio_str2list(ratio_str:str, normalize=1, split_char=":"):
    """比例字符串转换为list, 示例: 
        '5:3:2' => [.5, .3, .2]

    Arguments:
        ratio_str {str} -- 比例字符串(缺省以':'分隔)

    Keyword Arguments:
        normalize {int} -- 是否正则化 (总和等于 1) (default: {1})
        split_char {str} -- 分割字符 (default: {":"})

    Returns:
        list -- [float1, float2, ...]
    """
    ratio = [float(x) for x in ratio_str.split(split_char)]

    if normalize:
        ratio = ratio_normalize(ratio)

    return ratio


def ratio_split(sum_val, ratio, amend_sum_to_dim=-1):
    """按比例切割数字, 例如:
        (1999, (7, 6, 5)) == [777, 666, 556]
        (1999, '7:6:5') == [777, 666, 556]
        (1999, (7, 6, 5), 1) == [777, 667, 555]

    Arguments:
        sum_val {int} -- 总数
        ratio {str|tuple|list} -- 切割比例, 格式: 字符串以':'分隔, 或list/tuple

    Keyword Arguments:
        amend_sum_to_dim {int} -- 四舍五入部分补充到哪一维, 缺省最后一维 (default: {-1})

    Returns:
        list -- [count1, count2, ...]
    """
    if isinstance(ratio, str):
        ratio = ratio_str2list(ratio)
    else:
        ratio = ratio_normalize(ratio)

    counts = [round(x * sum_val) for x in ratio]
    counts[amend_sum_to_dim] += sum_val - sum(counts)
    
    return counts