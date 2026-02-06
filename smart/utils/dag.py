from collections import OrderedDict


class DagCycleErr(BaseException):
    @staticmethod
    def raise_err(cycle):
        raise DagCycleErr('dag has cycle: {}'.format(' -> '.join(map(str, cycle))))


def dag_dependance_set2dict(dependance_set:set, next_as_key=True) -> dict:
    """依赖关系集合转字典
    
    Arguments:
        dependance_set {set} -- {(prev_key, next_key)}
    
    Returns:
        dict -- if next_as_key is True, struct is {next_key: [prev_key]}; otherwise struct is {prev_key: [next_key]}
    """
    dep_dict = {}

    for prev_key, next_key in dependance_set:
        if not next_as_key:
            prev_key, next_key = next_key, prev_key

        if next_key not in dep_dict:
            dep_dict[next_key] = []
        
        dep_dict[next_key].append(prev_key)
    
    return dep_dict


def dag_find_cycle(dependance_set):
    dep_dict = dag_dependance_set2dict(dependance_set)
    
    safe_keys = set()

    def find_cycle(curr_key, key_chain = tuple()):
        if curr_key not in dep_dict:
            safe_keys.add(curr_key)
            return
        
        for dep_key in dep_dict[curr_key]:
            if dep_key in key_chain:
                return tuple(reversed(
                        (*key_chain[key_chain.index(dep_key):], curr_key, dep_key)
                    ))

            cycle = find_cycle(dep_key, key_chain = tuple((*key_chain, curr_key)))

            if cycle is not None:
                return cycle
        
        return None

    for key in dep_dict.keys():
        if key in safe_keys:
            continue

        cycle = find_cycle(key)

        if cycle is not None:
            return cycle
    
    return None


def dag_assert_no_cycle(dependance_set):
    cycle = dag_find_cycle(dependance_set)

    if cycle is not None:
        DagCycleErr.raise_err(cycle)


def dag_sort(key_obj_list:list, dependance_set, raise_err_on_cycle=False):
    if any((not key_obj_list, not dependance_set)):
        return key_obj_list

    with_sort_key_list = []
    key_idx_map = {}
    idx_key_map = {}
    # next_key: [prev_key]
    dep_dict = dag_dependance_set2dict(dependance_set)

    for i, key_obj in enumerate(key_obj_list):
        with_sort_key_list.append([None, i, key_obj])
        key_idx_map[key_obj[0]] = i
        idx_key_map[i] = key_obj[0]
    
    def __set_sort_key(i, chain=tuple()):
        sort_key, idx, key_obj = with_sort_key_list[i]

        if sort_key is not None and len(sort_key):
            # has setted
            return
        
        prev_keys = dep_dict.get(key_obj[0])

        if prev_keys is None:

            with_sort_key_list[i][0] = (idx,)
        else:

            prev_sort_keys = []
            _chain = tuple((*chain, i))

            for prev_key in prev_keys:
                prev_i = key_idx_map.get(prev_key)

                if prev_i is None or prev_i == i:
                    continue

                if prev_i in _chain:
                    if raise_err_on_cycle:
                        cycle = tuple(map(
                            lambda idx: idx_key_map.get(idx, idx),
                            (*_chain, prev_i)
                        ))
                        DagCycleErr.raise_err(cycle)
                    else:
                        continue

                __set_sort_key(prev_i, chain=_chain)
                prev_sort_keys.append(with_sort_key_list[prev_i][0])
            
            max_prev_sort_key = tuple()
            
            if prev_sort_keys:
                max_prev_sort_key = max(prev_sort_keys)
            
            with_sort_key_list[i][0] = tuple([*max_prev_sort_key, idx])

    for i in range(len(with_sort_key_list)):
        __set_sort_key(i)
    
    sorted_key_obj_list = []
    for sort_key, idx, key_obj in sorted(with_sort_key_list, key=lambda x: x[0]):
        sorted_key_obj_list.append(key_obj)

    return sorted_key_obj_list


class DagItemsTool:
    def __init__(self, id_key_name=None, prev_key_name=None, next_key_name=None):
        self.id_key_name = id_key_name
        self.prev_key_name = prev_key_name
        self.next_key_name = next_key_name
    
    def __iter_items(self, items):
        if isinstance(items, (list, tuple, set)):
            id_key_name = self.id_key_name
            assert id_key_name

            for item in items:
                yield item[id_key_name], item
        elif isinstance(items, dict):

            for key, val in items.items():
                yield key, val
        else:
            raise ValueError('illegal items type, expect list|tuple|set|dict, actual ' + str(type(items)) )
    
    def get_dependance_set(self, items):
        dependance_set = set()

        if not items:
            return dependance_set

        prev_key_name = self.prev_key_name
        next_key_name = self.next_key_name
        assert prev_key_name or next_key_name

        for key, obj in self.__iter_items(items):
            if prev_key_name:
                prev_keys = obj.get(prev_key_name) or []

                for prev_key in prev_keys:
                    dependance_set.add((prev_key, key))
            
            if next_key_name:
                next_keys = obj.get(next_key_name) or []

                for next_key in next_keys:
                    dependance_set.add((key, next_key))
        
        return dependance_set
    
    def sort_items(self, items, raise_err_on_cycle=False):
        key_obj_list = list(
            self.__iter_items(items)
        )

        dependance_set = self.get_dependance_set(items)

        return dag_sort(key_obj_list, dependance_set, raise_err_on_cycle=raise_err_on_cycle)
    
    def sort_item_dict(self, item_dict:dict, raise_err_on_cycle=False):
        dependance_set = self.get_dependance_set(item_dict)

        if not dependance_set:
            return item_dict

        ordered = OrderedDict()

        key_obj_list = item_dict.items()

        return OrderedDict(
            dag_sort(key_obj_list, dependance_set, raise_err_on_cycle=raise_err_on_cycle)
        )


