from typing import Any, List
from smart.utils.number import safe_parse_int
from smart.utils.dict import dict_find
from smart.utils.list import list_safe_iter
from smart.evals.__logger import logger


class ItemList:
    def __init__(self, data:list=[], **kwargs) -> None:
        self._data:List[List[dict]] = data or []
    
    def to_list(self):
        return self._data

    def fork(self, data:list=None, copy_data:bool=False):
        """使用data复制新的ItemList

        Args:
            data (list, optional): 新data. Defaults to None.
            copy_data (bool, optional): True的时候, 使用self._data复制新的ItemList, data参数失效. Defaults to False.

        Returns:
            ItemList: 新ItemList
        """
        if copy_data: data = self._data
        if data is None: data = []
        return ItemList(
            data=data
        )
    
    def filter(self, fn:callable):
        """返回fn(item)=True的数据

        Args:
            fn (callable): 回调函数, fn(item)->bool

        Returns:
            ItemList: 满足过滤条件的数据
        """
        item_list = [
            item
            for item in self._data
            if fn(item)
        ]
        new_obj = self.fork(
            data=item_list
        )
        return new_obj
    
    def filter_not(self, fn:callable):
        """返回fn(item)=False的数据

        Args:
            fn (callable): 回调函数, fn(item)->bool

        Returns:
            ItemList: 满足过滤条件的数据
        """
        item_list = [
            item
            for item in self._data
            if not fn(item)
        ]
        new_obj = self.fork(
            data=item_list
        )
        return new_obj
    
    def filter_all(self, fn_list:list):
        item_list = [
            item
            for item in self._data
            if all((fn(item) for fn in fn_list))
        ]
        new_obj = self.fork(
            data=item_list
        )
        return new_obj
    
    def filter_any(self, fn_list:list):
        item_list = [
            item
            for item in self._data
            if any((fn(item) for fn in fn_list))
        ]
        new_obj = self.fork(
            data=item_list
        )
        return new_obj
    
    def group(self, fn, group_keys:list=None):
        all_group = {}
        if group_keys:
            for key in group_keys:
                all_group[key] = self.fork(data=[])
        for item in self._data:
            group_name = fn(item)
            items:ItemList = all_group.get(group_name)
            if items is None: 
                items = ItemList(data=[])
                all_group[group_name] = items
            items._data.append(item)
        return all_group
    
    def multi_group(self, fn, group_keys:list=None):
        all_group = {}
        if group_keys:
            for key in group_keys:
                all_group[key] = self.fork(data=[])
        for item in self._data:
            group_name_list = fn(item)
            for group_name in list_safe_iter(group_name_list):
                items:ItemList = all_group.get(group_name)
                if items is None: 
                    items = ItemList(data=[])
                    all_group[group_name] = items
                items._data.append(item)
        return all_group

    def multi_group_item_iter_fn(self, group_fn):
        for item in self._data:
            group_name_list = group_fn(item)
            for group_name in list_safe_iter(group_name_list):
                yield group_name, item
    
    # def group_aggregate(self, group_fn, aggregate_view:AggregateView, key_path, cast_fn:callable=None):
    #     for group_name, item in self.multi_group_item_iter_fn(group_fn=group_fn):
    #         value = dict_find(item, key_path)
    #         if cast_fn:
    #             value = cast_fn(value)
    #         aggregate_view.add_value(value)

    def aggregate(self, fn, key_path, cast_fn:callable=None):
        if cast_fn:
            return fn((
                cast_fn(dict_find(item, key_path))
                for item in self._data
            ))
        else:
            return fn((
                dict_find(item, key_path)
                for item in self._data
            ))
     
    def __len__(self):
        return len(self._data)
    
    def __iter__(self):
        for item in self._data:
            yield item

    def __getitem__(self, name: str) -> Any:
        return self._data[name]


class ItemMatrix(ItemList):
    def __init__(self, data:list=[], column_names=None, **kwargs) -> None:
        if not column_names and len(data):
            column_names = list(range(len(data[0])))
        self._column_names = column_names
        super().__init__(data, **kwargs)
    
    def add_column(self, column_name:str=None):
        new_col_idx = len(self._column_names)
        if column_name is None:
            column_name = new_col_idx
        self._column_names.append(column_name)
        for row in self._data:
            row_len = len(row)
            if row_len < new_col_idx+1:
                row.extend([None] * (new_col_idx + 1 - row_len))
        return new_col_idx

    def join_items(self, item_list, column_name:str=None, id_key=None, match_columns:list=None, column_id_key_map:dict=None, append_no_match_item:bool=True):
        target_item_dict, conflict_ids = {}, []
        for item in item_list:
            item_id = dict_find(item, id_key)
            if item_id in target_item_dict:
                conflict_ids.append(item_id)
            target_item_dict[item_id] = item
        if conflict_ids:
            logger.warning('ItemMatrix.join_items has %s conflict_ids: %s...', len(conflict_ids), conflict_ids[:5])
        
        ori_columns = list(self._column_names)
        new_col_idx = self.add_column(column_name=column_name)
        new_col_size = len(self._column_names)

        if match_columns is None: 
            match_columns = list(range(len(ori_columns)))
        else:
            match_columns = list(match_columns)
        if new_col_idx in match_columns: 
            match_columns.remove(new_col_idx)
        for i, col_idx_or_name in enumerate(match_columns):
            if isinstance(col_idx_or_name, str):
                try:
                    col_idx = ori_columns.index(col_idx_or_name)
                    match_columns[i] = col_idx
                except ValueError:
                    raise "ItemMatrix miss column: " + str(col_idx_or_name)
                
        matched_id_set = set()
        column_id_key_map = column_id_key_map or {}
        for row in self._data:
            target_item = None
            for col_idx in match_columns:
                col_item = row[col_idx] if len(row) > col_idx else None
                if not col_item: continue
                col_id_key = column_id_key_map.get(col_idx, id_key)
                col_item_id = dict_find(col_item, col_id_key)
                target_item = target_item_dict.get(col_item_id)
                if target_item is not None: 
                    matched_id_set.add(col_item_id)
                    break
            row[new_col_idx] = target_item
        
        if append_no_match_item:
            for key, item in target_item_dict.items():
                if key in matched_id_set: continue
                # 添加为被匹配到的元素
                new_row = [None] * new_col_size
                new_row[new_col_idx] = item
                self._data.append(new_row)
        return self

    @staticmethod
    def from_list(item_list:ItemList, column_name:str=None):
        return ItemMatrix(
            data=[
                [item]
                for item in item_list
            ],
            column_names=[column_name]
        )
    
    @property
    def shape(self):
        return len(self._data), len(self._column_names)
    
    def get_column_idx(self, column_idx_or_name):
        if isinstance(column_idx_or_name, int):
            return column_idx_or_name
        else:
            for _idx, _name in enumerate(self._column_names):
                if _name == column_idx_or_name:
                    return _idx
            return safe_parse_int(column_idx_or_name)
    
    def column_data(self, column_idx_or_name):
        column_idx = self.get_column_idx(column_idx_or_name)
        return ItemList(
            data=[
                row[column_idx] if len(row) > column_idx else None
                for row in self._data
            ]
        )