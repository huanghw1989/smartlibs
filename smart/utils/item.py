from .list import list_to_tuple


class ItemGroupBy:
    def __init__(self, item_iter, keys, copy_item=True, only_group_val=False, no_pop_group_key=False):
        """item分组(仅适用于非大量数据)
        注意: 先在内存中接收完所有item, 再进行分组数据返回

        输入item:
        - {'id1': 1, 'id2': 'a', 'key1': '1', 'key2': [1]}
        - {'id1': 1, 'id2': 'a', 'key1': '2', 'key2': [2]}
        - {'id1': 1, 'id2': 'b', 'key1': '3', 'key2': [3]}

        输出item(group_key=['id1','id2']):
        - {'id1': 1, 'id2': 'a', 'item_list':[{'id1': 1, 'id2': 'a', 'key1': '1', 'key2': [1]}, {'id1': 1, 'id2': 'a', 'key1': '2', 'key2': [2]}]}
        - {'id1': 1, 'id2': 'b', 'item_list':[{'id1': 1, 'id2': 'b', 'key1': '3', 'key2': [3]}]}

        输出item(group_key=['id1','id2'], no_pop_group_key=False):
        - {'id1': 1, 'id2': 'a', 'item_list':[{'key1': '1', 'key2': [1]}, {'key1': '2', 'key2': [2]}]}
        - {'id1': 1, 'id2': 'b', 'item_list':[{'key1': '3', 'key2': [3]}]}
        
        Arguments:
            item_iter {iter} -- item生成器
            keys {list} -- 分组的key列表
        
        Keyword Arguments:
            copy_item {bool} -- 是否拷贝item; False将会改变item_iter返回的值 (default: {True})
            only_group_val {bool} -- 只返回group_val (default: {False})
            no_pop_group_key {bool} -- item_list的元素不pop分组key
        """
        self.item_iter = item_iter
        self.keys = keys
        self.key_iter = self.__key_iter_dict if isinstance(keys, dict) else self.__key_iter_list
        self.copy_item = copy_item
        self.only_group_val = only_group_val
        self.no_pop_group_key = no_pop_group_key

    def __key_iter_dict(self):
        for key, val in self.keys.items():
            yield key, val
    
    def __key_iter_list(self, defaultVal=None):
        for key in self.keys:
            yield key, defaultVal

    def __parse_item(self, item):
        if self.copy_item:
            item = item.copy()

        if self.no_pop_group_key:

            group_key = list_to_tuple(
                item.get(key, defaultVal)
                for key, defaultVal in self.key_iter()
            )
        else:

            group_key = list_to_tuple(
                item.pop(key, defaultVal)
                for key, defaultVal in self.key_iter()
            )

        return group_key, item
    
    def __iter_only_group_val(self, item_iter):
        all_key = set()

        for item in item_iter:
            group_key, other = self.__parse_item(item)

            if group_key not in all_key:
                all_key.add(group_key)
                yield group_key
    
    def __iter_group(self, item_iter):
        group = {}

        for item in item_iter:
            group_key, other = self.__parse_item(item)

            if group_key not in group:
                group[group_key] = []
                
            group[group_key].append(other)

        for group_key, item_list in group.items():
            yield group_key, item_list
    
    def __call__(self):
        """
        Yields:
            tuple -- 初始化参数only_group_val如果为True, 则返回group_val; 否则, 返回(group_val, item_list)
        """
        if self.only_group_val:
            yield from self.__iter_only_group_val(self.item_iter)
        else:
            yield from self.__iter_group(self.item_iter)



class ItemMergeFn:
    def __init__(self, item_iter, group_keys, group_idx_key, no_pop_group_key=True):
        """列表数据分组
        
        Arguments:
            item_iter {iter} -- item生成器
            group_keys {list} -- 分组的key列表
            group_idx_key {str} -- 分组idx的key
        
        Keyword Arguments:
            only_group_val {bool} -- 只返回group_val (default: {False})
            no_pop_group_key {bool} -- item_list的元素不pop分组key
        """
        self.item_iter = item_iter
        self.group_keys = group_keys
        self.group_idx_key = group_idx_key
        self.key_iter = self.__key_iter_dict if isinstance(group_keys, dict) else self.__key_iter_list
        self.no_pop_group_key = no_pop_group_key
        self.opt_copy_item = not no_pop_group_key
        self._group_data = None

    def __key_iter_dict(self):
        for key, val in self.keys.items():
            yield key, val
    
    def __key_iter_list(self, defaultVal=None):
        for key in self.group_keys:
            yield key, defaultVal

    def __parse_item(self, item):
        if self.opt_copy_item:
            item = item.copy()

        if self.no_pop_group_key:

            group_key = list_to_tuple(
                item.get(key, defaultVal)
                for key, defaultVal in self.key_iter()
            )
        else:

            group_key = list_to_tuple(
                item.pop(key, defaultVal)
                for key, defaultVal in self.key_iter()
            )

        return group_key, item
    
    def __iter_group(self, item_iter, group_data):
        idx_key = self.group_idx_key

        for item in item_iter:
            group_key, other = self.__parse_item(item)
            idx, count = item.get(idx_key) or (None, None)

            if not count or count < 2:
                yield group_key, [other]
                continue

            if group_key not in group_data:
                group_data[group_key] = {}
            
            item_dict = group_data[group_key]
            item_dict[idx] = other
            if len(item_dict.keys()) >= count:
                item_list = [item_dict[i] for i in sorted(item_dict.keys())]
                del group_data[group_key]
                yield group_key, item_list
        
        # 剩余的数据
        for group_key in tuple(group_data.keys()):
            item_dict = group_data.pop(group_key)
            item_list = [item_dict[i] for i in sorted(item_dict.keys())]
            yield group_key, item_list
    
    def __call__(self):
        """
        Yields:
            tuple -- 返回(group_val, item_list)
        """
        self._group_data = group_data = {}
        yield from self.__iter_group(self.item_iter, group_data)