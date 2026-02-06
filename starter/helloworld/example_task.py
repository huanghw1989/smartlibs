"""Ch1. Quick Start in 1min
Target: Learn Task Expression.

Task Expression Example: example_task.range~attach,st~log

How-to-run: python -m smart.auto.run starter.helloworld.auto task:example_task.range~attach,st~log
            smart_auto starter.helloworld.auto task:example_task.range~attach,st~log

Bind Arg Example:
    python -m smart.auto.run starter.helloworld.auto task:example_task.range~attach,st~log --bind_arg.example_task.range.end=20

Debug in VSCode: python -m smart.auto.run_debug starter.helloworld.auto task:example_task.range~attach,st~log
"""
import time, random, datetime, os

from smart.auto import TreeMultiTask

from .utils import logger, auto_load, task_hook


@auto_load.task('example_task', alias=['example'])
class ExampleTask(TreeMultiTask):

    @task_hook.before_task()
    def check_state(self, no_pass=None, no_pass_idx=None):
        state = self.context.state('check_state')
        task_idx = state.set_fn(
            'task_idx', lambda val:(val or 0) + 1)

        logger.info('### ExampleTask.check_state pid=%s, idx=%s, pass=%s', 
                os.getpid(), task_idx, not no_pass)

        if no_pass:
            # stop tree
            self.stop_task(end_all=True)
            return
        elif no_pass_idx == task_idx:
            # stop task
            self.stop_task()
            return

        range_step = int(task_idx)

        self.context.response().set(('hi', task_idx), {
            'from': 'ExampleTask.check_state',
            'step': range_step,
            'time': time.time()
        })

        # join args still work
        # 不能返回无法pickle的对象, 否则会导致windows无法开启多进程
        return {
            'step': range_step
        }

    @task_hook.after_task()
    def on_end(self):
        logger.info('ExampleTask.on_end pid=%s', os.getpid())

        if self.is_stop_task():
            return

        for i, item in enumerate(self.recv_data(no_data=False)):
            logger.debug('clean %s item: %s', i, item)
            
        logger.debug('ExampleTask on_end done')

    @task_hook.before_task()
    def dispatch(self, tree_name=None):

        return {
            'tree_name': tree_name or 'range'
        }
    
    @auto_load.method(['example_task.default'])
    def range(self, start:int=0, end:int=10, step:int=1):
        logger.info('ExampleTask.range %s', (start, end, step))
        # self.context.state('test').set('range', (start, end, step))

        return {
            'item_iter': [
                {'id': i, 'ts': time.time()}
                for i in range(start, end, step)
            ]
        }
    
    def attach(self, item_iter=None, attach_time=False):
        logger.info('ExampleTask.attach %s', (attach_time,))
        item_iter = item_iter if item_iter else self.recv_data()
        sum = 0
        item_list = []
        for item in item_iter:
            sum += item['id']
            item['sum'] = sum
            item_list.append(item)
            if attach_time:
                d = datetime.datetime.fromtimestamp(item['ts'])
                item['time'] = d.strftime("%Y-%m-%d %H:%M:%S.%f")
        return {
            'item_iter': item_list
        }

    def st(self, item_iter=None):
        item_iter = item_iter if item_iter else self.recv_data()
        num_items = 0
        ts = None
        for item in item_iter:
            num_items += 1
            if ts is None: 
                ts = (item['ts'], item['ts'])
            else:
                ts = (min(item['ts'], ts[0]), max(item['ts'], ts[1]))
        return {
            'st': {
                'num_items': num_items,
                'item_ts_during': ts[1]-ts[0] if ts else 0
            }
        }

    def log(self, item_iter=None, st=None):
        item_iter = item_iter if item_iter else self.recv_data()
        for item in item_iter:
            logger.info('test_recv: %s', item)
        if st:
            logger.info('st: %s', st)
    
    def send(self, item_iter=None):
        item_iter = item_iter if item_iter else self.recv_data()
        for item in item_iter:
            self.send_data(item)


@auto_load.func_task('helloworld.example_recv', config='example_task.recv')
def example_recv_task(task):
    for item in task.recv_data():
        print(item)