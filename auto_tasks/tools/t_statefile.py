import os, json, time

from smart.auto.tree import TreeMultiTask

from smart.utils import path_join

from .__utils import auto_load, logger, task_hook


@auto_load.task('tools.statefile')
class StateFileTask(TreeMultiTask):
    @task_hook.before_task()
    def read(cls, file_name, file_path=None, root_dir=None):
        """读取状态文件
        放在ETL-extract步骤之前, 把读取到的state_dict传给extract函数.
        state_dict有last, doing和update_ts字段, update_ts是任务完成的时间，非数据库里的数据条目的timestamp.
        last存储上一次任务执行的end函数收到的item数据中，start接收顺序最大的数据.
        doing存储了last指针之前，调用了start函数，但没执行到end函数到数据. 

        Args:
            file_name (str): 状态文件的文件名
            file_path (str, optional): 状态文件的目录. Defaults to None.
            root_dir (str, optional): 状态文件的根目录. Defaults to None.

        Returns:
            dict: {state_dict:{last, doing}}
        """
        state_file_path = path_join(root_dir, file_path, file_name, auto_mkdir=True)

        if os.path.exists(state_file_path):
            with open(state_file_path, 'r', encoding='utf8') as f:
                state_dict = json.load(f)
        else:
            state_dict = {}
        
        if not isinstance(state_dict, dict):
            state_dict = {}
        
        ctx_state = cls.context.state('statefile')

        ctx_state.set('init', state_dict)
        ctx_state.set('file_path', state_file_path)
        doing_list = cls.context.store.list('__statefile_doing')

        # logger.debug('state_dict init: %s', state_dict)
        
        return {
            'state_dict': state_dict
        }
    
    def start(cls, id_keys, item_iter=None, item_iter_fn=None):
        """开始处理数据前调用, 在内存变量中记录正在处理的数据.
        item_iter应当是有序的(根据id_keys的值升序或降序)

        Args:
            id_keys (str|list): item的主键. 联合主键可以用','拼接, 也可以用数组传参. 
            item_iter {generator} -- 输入数据生成器 (default: {None})
            item_iter_fn {callable} -- 输入数据生成器构造函数 (default: {None})
        """
        _item_iter = item_iter or (item_iter_fn or cls.recv_data)()

        if isinstance(id_keys, str):
            id_keys = list(map(lambda x:x.strip(), id_keys.split(',')))
        elif isinstance(id_keys, (list, tuple)):
            id_keys = list(id_keys)
        else:
            raise ValueError('illegal id_keys')

        ctx_state = cls.context.state('statefile')
        ctx_state.set('item_id_keys', id_keys)

        doing_list = cls.context.store.list('__statefile_doing')
        
        def _item_iter_fn():
            for item in _item_iter:
                val = tuple((item.get(key) for key in id_keys))
                doing_list.append(val)
                yield item
        
        if item_iter:
            return {
                'item_iter': _item_iter_fn()
            }
        elif item_iter_fn:
            return {
                'item_iter_fn': _item_iter_fn
            }
        else:
            for item in _item_iter_fn():
                cls.send_data(item)
    
    def end(cls, item_iter=None, item_iter_fn=None, save_step=100, print_save=0):
        """处理数据完成后调用, 同步信息到状态文件.
        item_iter可以支持乱序. 
        一般来说, 如果item_iter是根据start函数的顺序发送过来, 那么状态文件里的doing字段应当是空数组;
        如果item_iter是乱序的(处理函数启用了多进程/多线程), 那么状态文件里的doing字段会有值. 
        注意：start和end收到的数据必须是一一对应，中间步骤不能将一条item拆分成多条或丢弃item

        Args:
            item_iter {generator} -- 输入数据生成器 (default: {None})
            item_iter_fn {callable} -- 输入数据生成器构造函数 (default: {None})
            save_step (int, optional): 每隔若干步同步状态到文件. Defaults to 100.
            print_save (int, optional): 是否打印保存状态到日志. Defaults to 0.
        """
        _item_iter = item_iter or (item_iter_fn or cls.recv_data)()

        ctx_state = cls.context.state('statefile')
        state_file_path = ctx_state.wait('file_path', timeout=60)
        item_id_keys = ctx_state.wait('item_id_keys', timeout=60)

        doing_list = cls.context.store.list('__statefile_doing')

        doing_set = set()
        last = None

        def _save_statefile():
            state_dict = {
                'last': last,
                'doing': list(doing_set),
                'update_ts': time.time()
            }

            state_str = json.dumps(state_dict, ensure_ascii=False)

            with open(state_file_path, 'w', encoding='utf8') as f:
                f.write(state_str)
            
            return state_dict

        for i, item in enumerate(_item_iter):
            done = tuple((item.get(key) for key in item_id_keys))

            if done in doing_set:
                doing_set.remove(done)
            else:
                while True:
                    try:
                        doing = doing_list.pop(0)
                    except IndexError:
                        logger.warning("StateFileTask.end recv item(%s) no in doing_list", done)
                        break
                    # 这里假设doing_list是按顺序排序
                    last = doing
                    if doing == done:
                        break
                    else:
                        doing_set.add(doing)
            
            if (i+1) % save_step == 0:
                state_dict = _save_statefile()
                if print_save:
                    if ((i+1) / save_step) % print_save == 0:
                        logger.debug('statefile(step %d) save %s', i+1, state_dict)
        
        _save_statefile()
        logger.debug('statefile save path: %s', state_file_path)
        

