import json, time, pprint
from collections import Counter

from smart.auto.tree import TreeMultiTask

from .__utils import auto_load, logger


@auto_load.task('tools.tool', alias=['tools__tool'])
class ToolTask(TreeMultiTask):
    def range(self, size:int=10, step:int=1, start:int=0, end=None, idx_key='i', time_key=None):
        """make range items
        
        Keyword Arguments:
            size {int} -- 数据条数 (default: {10})
            step {int} -- range 步长 (default: {1})
            start {int} -- range 起始 (default: {0})
            end {[type]} -- range 结束, 如果设置end, size参数将无效 (default: {None})
            idx_key {str} -- range 值所在的键; None 表示直接返回 int 数据 (default: {'i'})
            time_key {[type]} -- 数据创建时间戳所在的键, None表示不添加创建时间; idx_key为None时, time_key值无效 (default: {None})
        
        Returns:
            dict -- {item_iter, item_iter_fn}
        
        Yields:
            dict|int -- idx_key不为空时, yield {idx_key, time_key}; idx_key为空时, yield int
        """
        if end is None:
            end = start + step * size
        
        logger.debug('tools__tool.range %s %s', (size, step, start, end), idx_key)

        def item_iter_fn():
            for i in range(start, end, step):
                if idx_key is None:
                    yield i
                else:
                    item = {idx_key:i}
                    if time_key:
                        item[time_key] = time.time()
                    yield item

        return {
            'item_iter': item_iter_fn(),
            'item_iter_fn': item_iter_fn
        }
    
    def throttle(self, speed:float=100, batch:int=1, interval:float=None, log_step:int=10000, item_iter=None, item_iter_fn=None):
        """节流器

        获取数据的来源三选1: item_iter > item_iter_fn > 数据管道
        
        Keyword Arguments:
            speed {float} -- unit: examples/second (default: {100})
            batch {int} -- 每batch条数据执行一次节流器 (default: {1})
            interval {float} -- 两次节流器运行的最小时间间隔, 缺省batch/speed; 如不为空, speed参数将失效 (default: {None})
            log_step {int} -- 每step条数据打印一次sleep统计, 缺省为10000
            item_iter {generator} -- 输入数据生成器 (default: {None})
            item_iter_fn {callable} -- 输入数据生成器构造函数 (default: {None})
        
        Returns:
            dict -- {item_iter, item_iter_fn}
        """
        item_iter = item_iter or (item_iter_fn or self.recv_data)()

        if interval is None:
            interval = 1.0*batch/speed
        
        logger.debug('ToolTask.throttle interval=%s, batch=%s', interval, batch)

        def item_iter_fn():
            prev_time = time.time()
            sleep_total = sleep_sum = 0.0
            i = 0
            for i, item in enumerate(item_iter):
                yield item

                if (i + 1) % batch == 0:
                    curr_time = time.time()
                    sleep_time = interval - curr_time + prev_time

                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        sleep_sum += sleep_time
                        prev_time = curr_time + sleep_time
                    else:
                        prev_time = curr_time
                
                if log_step:
                    if (i + 1) % log_step == 0:
                        logger.info('ToolTask.throttle sleep %s seconds (%s items)', sleep_sum, i+1)
                        sleep_total += sleep_sum
                        sleep_sum = 0
            
            logger.info('ToolTask.throttle total sleep %s seconds (%s items)', sleep_total+sleep_sum, i+1)
        
        return {
            'item_iter': item_iter_fn(),
            'item_iter_fn': item_iter_fn
        }
    
    @auto_load.func_task('tools.send')
    def send(self, item_iter=None, item_iter_fn=None, send_kwargs={}):
        """发送数据到任务单元之间的数据管道(向下游任务的输入数据管道)

        获取数据的来源2选1: item_iter > item_iter_fn
        
        Keyword Arguments:
            item_iter {generator} -- 输入数据生成器 (default: {None})
            item_iter_fn {callable} -- 输入数据生成器构造函数 (default: {None})
            send_kwargs {dict} -- 数据管道send函数的参数选项, 支持{block, timeout} (default: {{}})
        """
        if not item_iter and item_iter_fn:
            item_iter = item_iter_fn()

        if item_iter:
            for item in item_iter:
                self.send_data(item, **send_kwargs)
    
    def __groupable_val(self, val):
        if val is None:
            return val

        if isinstance(val, (str, bytes, int, float, complex)):
            return val
        
        if isinstance(val, (tuple, list)):
            return tuple((
                self.__groupable_val(c_val)
                for c_val in val
            ))
        
        return str(val)
    
    def counter(self, item_iter=None, item_iter_fn=None, group_key=None, delay=0):
        """数据统计

        支持统计数据总数, 分组数据总数

        获取数据的来源三选1: item_iter > item_iter_fn > 数据管道
        
        Keyword Arguments:
            item_iter {generator} -- 输入数据生成器 (default: {None})
            item_iter_fn {callable} -- 输入数据生成器构造函数 (default: {None})
            group_key {str|list} -- 分组统计; list类型表示从多个字段取数据作为分组值 (default: {None})
            delay {int} -- 每100条数据sleep delay seconds; 仅调试使用的字段, 建议用 throttle 函数 (default: {0})
        
        Returns:
            dict -- {counter}
        """
        item_iter = item_iter or (item_iter_fn or self.recv_data)()
        counter = Counter()

        for i, item in enumerate(item_iter):
            counter['num_items'] += 1

            if group_key:
                if isinstance(group_key, list):
                    group_val = tuple((
                        self.__groupable_val(item.get(k))
                        for k in group_key
                    ))
                else:
                    group_val = self.__groupable_val(item.get(group_key))

                counter[('group', group_val)] += 1

            if delay and i and i % 100 == 0:
                time.sleep(float(delay))
        
        logger.info('ToolTask.counter: %s', pprint.pformat(counter))

        return {
            'counter': counter,
        }