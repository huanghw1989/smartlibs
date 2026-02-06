import os, json, logging

from smart.auto import TreeMultiTask, AutoLoad
from smart.utils import list_safe_iter, path_join

from .__utils import auto_load, logger


@auto_load.task('jsonl__file')
class JsonlFileTask(TreeMultiTask):
    def __resolve_file_name_keys(self, file_name_keys, file_name_idx_or_key=None):
        if isinstance(file_name_keys, str):
            file_name_key_list = [k.strip() for k in file_name_keys.split(',')]
        else:
            file_name_key_list = file_name_keys
            
        if isinstance(file_name_idx_or_key, int):
            yield file_name_key_list[file_name_idx_or_key]
        elif file_name_idx_or_key:
            yield file_name_idx_or_key
        else:
            yield from file_name_key_list

    def pattern_read(self, file_name_keys, file_name_pattern:dict='{}', dir_path=None, file_open_opts=None, root_dir=None, group_key='_group', file_path=None):
        """读取多份jsonl文件

        Arguments:
            file_name_keys {list} -- 文件名的键列表

        Keyword Arguments:
            file_name_pattern {str} -- 文件名模版, 使用'{}'占位file_name_key (default: {'{}'})
            dir_path {str} -- 文件目录路径 (default: {None})
            file_open_opts {dict} -- 打开文件选项 (default: {None})
            root_dir {str} -- 根路径 (default: {None})
            group_key {str} -- item的分组键, 值为file_name_key (default: {'_group'})
            file_path {str} -- 弃用, 请使用dir_path代替 (default: {None})

        Returns:
            dict -- {item_iter_fn}
        """
        _file_name_keys = file_name_keys
        dir_path = dir_path or file_path
        file_open_opts = {'mode': 'r', 'encoding': 'utf8', **(file_open_opts or {})}

        def item_iter_fn(file_name_idx_or_key = None, file_name_keys=None):
            file_name_key_list = self.__resolve_file_name_keys(file_name_keys or _file_name_keys, file_name_idx_or_key)
            
            for file_name_key in file_name_key_list:
                num_items = 0
                file_name = file_name_pattern.format(file_name_key)
                file = path_join(root_dir, dir_path, file_name)

                if not os.path.exists(file):
                    logger.warning('JsonlFileTask.pattern_read: no found file %s', file)
                    continue

                with open(file, **file_open_opts) as f:
                    for line in f:
                        if not line:
                            continue
                        item = json.loads(line)
                        if isinstance(item, dict) and group_key:
                            item[group_key] = file_name_key
                        yield item
                        num_items += 1
                logger.debug('JsonlFileTask.pattern_read %s items from %s', num_items, file)
                
        return {
            'item_iter_fn': item_iter_fn
        }
    
    def read(self, file_name, dir_path=None, file_open_opts:dict=None, root_dir=None, file_path=None):
        """读取jsonl文件

        Arguments:
            file_name {str} -- 文件名

        Keyword Arguments:
            dir_path {str} -- 文件目录路径 (default: {None})
            file_open_opts {dict} -- 打开文件选项 (default: {None})
            root_dir {str} -- 根路径 (default: {None})
            file_path {str} -- 弃用, 请使用dir_path代替 (default: {None})

        Returns:
            dict -- {item_iter_fn}
        """
        dir_path = dir_path or file_path
        file = path_join(root_dir, dir_path, file_name)
        file_open_opts = {'mode': 'r', 'encoding': 'utf8', **(file_open_opts or {})}

        def item_iter_fn():
            with open(file, **file_open_opts) as f:
                for line in f:
                    item = json.loads(line)
                    yield item
        
        return {
            'item_iter_fn': item_iter_fn
        }
    
    def write(self, file_name, dir_path=None, file_open_opts:dict=None, root_dir=None, item_iter=None, item_iter_fn=None, recv_args={}, file_path=None):
        """写jsonl文件

        Arguments:
            file_name {str} -- 文件名

        Keyword Arguments:
            dir_path {str} -- 文件目录路径 (default: {None})
            file_open_opts {dict} -- 打开文件选项 (default: {None})
            root_dir {str} -- 根路径 (default: {None})
            item_iter {generator} -- item生成器 (default: {None})
            item_iter_fn {callable} -- item生成器构造函数; item_iter非空时, 本参数无效 (default: {None})
            recv_args {dict} -- 接收数据函数的参数选项; item_iter非空时, 本参数无效 (default: {{}})
            file_path {str} -- 弃用, 请使用dir_path代替 (default: {None})
        """
        assert file_name
        dir_path = dir_path or file_path
        file = path_join(root_dir, dir_path, file_name, auto_mkdir=True)
        file_open_opts = {'mode': 'w', 'encoding': 'utf8', **(file_open_opts or {})}
        logger.info('jsonl__file.write %s', file_name)

        item_iter = item_iter or (item_iter_fn or self.recv_data)(**recv_args)

        count = 0
        with open(file, **file_open_opts) as f:
            for item in item_iter:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
                count += 1
        
        logger.debug('jsonl__file.write %s items to %s', count, file_name)

