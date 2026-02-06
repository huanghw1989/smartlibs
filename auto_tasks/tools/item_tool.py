import time

from smart.auto.tree import TreeMultiTask
from smart.utils.item import ItemGroupBy, ItemMergeFn

from .__utils import auto_load


@auto_load.task('tools.item_tool')
class ItemToolTask(TreeMultiTask):
    def merge(self, item_iter=None, item_iter_fn=None, 
                group_key=None, group_idx_key='group_idx', key_item_list='item_list'):
        """item合并
        注意: item需要带(组内idx,size)

        输入item:
        - {'id1': 1, 'id2': 'a', 'group_idx': (0, 2), 'key1': '1', 'key2': [1]}
        - {'id1': 1, 'id2': 'b', 'group_idx': (0, 1), 'key1': '3', 'key2': [3]}
        - {'id1': 1, 'id2': 'a', 'group_idx': (1, 2), 'key1': '2', 'key2': [2]}

        输出item(group_key=['id1','id2']):
        - {'id1': 1, 'id2': 'b', 'item_list':[{'id1': 1, 'id2': 'b', 'group_idx': (0, 1), 'key1': '3', 'key2': [3]}]}
        - {'id1': 1, 'id2': 'a', 'item_list':[{'id1': 1, 'id2': 'a', 'group_idx': (0, 2), 'key1': '1', 'key2': [1]}, {'id1': 1, 'id2': 'a', 'group_idx': (1, 2), 'key1': '2', 'key2': [2]}]}
        
        Args:
            item_iter (generator, optional): 输入数据生成器 (default: {None})
            item_iter_fn (callable, optional): 输入数据生成器构造函数 (default: {None})
            group_key (str|list, 非空): 分组的key. Defaults to None.
            group_idx_key (str): 组内idx和size数据的key. Defaults to 'group_idx'.
            no_pop_group_key (bool, optional): 是否从item中pop出group_key的数据. Defaults to True.

        Returns:
            dict: grouped_item
        """
        assert group_key and group_idx_key
        _item_iter = item_iter or (item_iter_fn or self.recv_data)()

        if isinstance(group_key, str):
            group_keys = [group_key]
        else:
            group_keys = group_key

        def _merge_fn():
            _group_item_iter = ItemMergeFn(
                _item_iter, group_keys, group_idx_key
            )()
            for group_tuple, item_list in _group_item_iter:
                group_dict = dict(
                    zip(group_keys, group_tuple)
                )
                group_dict[key_item_list] = item_list
                yield group_dict

        return {
            "item_iter": _merge_fn(),
            "item_iter_fn": _merge_fn
        }
    
    def group(self, item_iter=None, item_iter_fn=None, 
                group_key=None, key_item_list='item_list', no_pop_group_key:bool=True):
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
        
        Args:
            item_iter {generator} -- 输入数据生成器 (default: {None})
            item_iter_fn {callable} -- 输入数据生成器构造函数 (default: {None})
            group_key (str|list, optional): 分组的key. Defaults to None.
            no_pop_group_key (bool, optional): 是否从item中pop出group_key的数据. Defaults to True.

        Returns:
            dict: grouped_item
        """
        assert group_key
        _item_iter = item_iter or (item_iter_fn or self.recv_data)()
        copy_item = not no_pop_group_key
        if isinstance(group_key, str):
            keys = [group_key]
        else:
            keys = group_key
        
        def _group_item_fn():
            _group_item_iter = ItemGroupBy(_item_iter, 
                keys=keys, 
                copy_item=copy_item, 
                no_pop_group_key=no_pop_group_key)()
            
            for group_tuple, item_list in _group_item_iter:
                group_dict = dict(
                    zip(keys, group_tuple)
                )
                group_dict[key_item_list] = item_list
                yield group_dict

        return {
            "item_iter": _group_item_fn(),
            "item_iter_fn": _group_item_fn
        }