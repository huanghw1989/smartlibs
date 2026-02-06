import time, functools, typing, sys
import multiprocessing as mp
from smart.auto.exec.worker import worker_cls_builder, BaseWorker

from smart.utils.process import on_process_init
from smart.utils.list import list_safe_get
from smart.utils.number import safe_parse_int
from smart.auto.constants import Constants
from smart.auto.tree import TreeTask
from smart.auto.meta import TaskMeta
from smart.auto.pip.cmd import Command, CommandType, end_cmd
from smart.auto.ctx.tree_context import TreeContext
from smart.auto.exec.fn_chain import FnChain
from smart.auto.__logger import logger


class TaskPod:
    Opt_Worker_Start_Interval = 0.01
    Opt_Restart_Interval = 1

    def __init__(self, context:TreeContext, task_meta:TaskMeta, fn_chain:FnChain,
                worker_mode:str=None, worker_num:int=None, restart=None, **kwargs) -> None:
        self.context = context
        self.task_meta = task_meta
        self.fn_chain = fn_chain
        self.worker_mode = worker_mode
        self.worker_num = worker_num
        self.worker_done_count = mp.Value('i', 0)
        self.worker_list:typing.List[BaseWorker] = []
        self._to_kill_workers:typing.List[BaseWorker] = []
        self.__started = False
        if restart in (True, 'True', 1, 'true'):
            restart = 'on-error'
        self._policy_restart = (restart or 'no').split(':')
        self._opt = kwargs
    
    @property
    def task_class(self) -> typing.Type[TreeTask]:
        return self.task_meta.task_class
    
    @property
    def task_obj(self) -> TreeTask:
        return self.task_meta.task_obj
    
    def all_task_obj(self):
        yield self.task_obj
        for _task_obj in self.task_obj._join_task_list:
            yield _task_obj
    
    def get_worker_mode(self):
        return Constants.DEFAULT_WORKER_MODE if self.worker_mode is None else self.worker_mode

    def __task_repr(self, task_meta=None):
        task_meta = task_meta or self.task_meta
        return (task_meta.task_key, task_meta.task_class_path or task_meta.task_class) if task_meta else 'unknown task'

    def _clean_pip_in(self):
        """清空管道数据
        如果管道残留数据, 进程可能不会正常退出. 
        """
        pip_in = self.task_obj.pip_in

        if pip_in:
            clean_num = pip_in.clean()
            if clean_num:
                logger.debug('%s clean_pip_in %d items', self.task_class, clean_num)

    def _on_worker_done(self, worker_num, send_end_cmd=True, clean_pip_in=True, context:TreeContext=None):
        """任务结束回调

        当任务的最后一个工作进程结束时, 自动向后置任务的接收数据管道发送 end_cmd. 
        end_cmd 用于 recv_data 函数结束生成器, 无需任务函数处理. 

        Arguments:
            worker_num {int} -- 工作进程数量

        Keyword Arguments:
            send_end_cmd {bool} -- 是否向后置任务发送 end_cmd (default: {True})
            clean_pip_in {bool} -- 任务结束时是否清理输入管道的残留数据 (default: {True})
        """
        done_count = self.worker_done_count

        with done_count.get_lock():
            done_count.value += 1

            if done_count.value >= worker_num:
                if worker_num > 1:
                    logger.debug('%s workers all done(%d/%d)', self.task_class, done_count.value, worker_num)

                if send_end_cmd:
                    self.task_obj.send_data(end_cmd)
                
                if clean_pip_in:
                    self._clean_pip_in()

    def _on_queue_end(self, command, worker_num=1):
        # 接收到end命令, 需要转发给其它进程
        # print('__on_queue_end', command.args)
        # logger.debug('%s queue end (pid %d)', self.task_class, os.getpid())
        if command.args.get('no_forward'):
            return

        for i in range(worker_num-1):
            self.task_obj.pip_in.send(Command(
                type=CommandType.end, 
                no_forward=True
            ))
            
    def is_done(self):
        worker_num = self.worker_num
        if worker_num is None: worker_num = 1

        return self.worker_done_count.value >= worker_num
    
    def _task_counter(self, key, incr=0):
        counter_state = self.context.state(self.task_obj.task_key)
        return counter_state.set_fn(('counter', key), lambda val:(val or 0)+incr)
    
    def _err_cb(self):
        task_error_count = self._task_counter('task_error', incr=1)
        self.task_obj.worker_state.update(
            task_error_count = task_error_count
        )
        error_count = self.task_obj.worker_state.incr('error_count')

        _restart = self._policy_restart[0]
        if _restart == 'always':
            return True
        elif _restart in ('on-error', 'on-failure'):
            restart_max_num = safe_parse_int(list_safe_get(self._policy_restart, 1))
            if restart_max_num is None or error_count <= restart_max_num:
                return True
        return False
    
    def run_task(self, send_end_cmd=True, on_task_done:callable=None, worker_idx=None, remote_debug=False):
        worker_mode = self.get_worker_mode()
        if remote_debug:
            port = int(remote_debug)
            from smart.utils import remote_debug
            remote_debug.enable_remote_debug(port=(port if port > 1000 else None))
            
        if worker_idx is not None and worker_mode == 'process':
            on_process_init()

        start_time = time.monotonic()
        try:
            while True:
                try:
                    task_run_count = self._task_counter('task_run', incr=1)
                    task_error_count = self._task_counter('task_error', incr=0)
                    self.task_obj.worker_state.update(
                        worker_idx=worker_idx,
                        task_run_count=task_run_count,
                        task_error_count=task_error_count
                    )
                    # 执行任务函数
                    fn_chain = self.fn_chain
                    fn_chain.run_chain(
                        fn_filter=lambda fn_item: fn_item.fn_type in (None, '', 'task')
                    )
                except Exception as e:
                    b_run = self._err_cb()
                    if b_run:
                        logger.exception(e)
                        logger.info("TaskPod restart %s#%s after %s second", self.task_obj.task_key, worker_idx or 0, self.Opt_Restart_Interval)
                        time.sleep(self.Opt_Restart_Interval)
                        continue
                    else:
                        raise e
                break
        finally:
            if send_end_cmd:
                self.task_obj.send_data(end_cmd)
            if on_task_done:
                on_task_done()
        during = time.monotonic() - start_time
        logger.debug('Task %s %s took %f seconds', self.task_class, self.task_meta.task_key, during)

    def start(self, send_end_cmd=True, clean_pip_in=True, remote_debug=False):
        if self.__started:
            logger.warning("TaskPod.start should call once")
            return
        self.__started = True

        worker_list = self.worker_list
        task_key = self.task_meta.task_key
        context = self.context
        context.run_stage = 'task'
        
        if context.is_stop_task(task_key=task_key, end_all=True):
            logger.info('TreeTaskExecutor.end(by context.stop_task)')
            self.worker_done_count.value = worker_num or 1
            if clean_pip_in:
                self._clean_pip_in()
            return

        worker_mode, worker_num = self.get_worker_mode(), self.worker_num
        enable_worker = isinstance(worker_num, int) and worker_num > 0

        if not enable_worker:
            self.run_task(send_end_cmd=send_end_cmd, remote_debug=remote_debug)
            self.worker_done_count.value = worker_num or 1

            if clean_pip_in:
                self._clean_pip_in()
            return

        for worker_idx in range(worker_num):
            remote_debug = remote_debug if worker_idx == 0 else False
            _worker_name = task_key
            if worker_idx:
                _worker_name += '#'+str(worker_idx)
                time.sleep(self.Opt_Worker_Start_Interval)
            
            self.task_obj.options['worker_idx'] = worker_idx
            self.task_obj.pip_in.on_end = functools.partial(self._on_queue_end, worker_num=worker_num)

            _on_worker_done = functools.partial(
                self._on_worker_done, 
                worker_num=worker_num, 
                send_end_cmd=send_end_cmd, 
                clean_pip_in=clean_pip_in,
                context=context )

            WorkerCls = worker_cls_builder(worker_mode)
            worker = WorkerCls(target=self.run_task, args=(
                False, _on_worker_done, worker_idx, remote_debug
            ), name=_worker_name)
            worker.start()

            logger.debug('# %s %s-%s started, id=%s', WorkerCls.__name__, self.__task_repr(), worker_idx, worker.ident)
            worker_list.append(worker)

    def join(self):
        worker_list = self.worker_list
        task_meta = self.task_meta
        for worker in worker_list:
            if worker.is_alive():
                # logger.debug('await worker %s', task_meta.task_key)
                for i in range(1, sys.maxsize):
                    if not i % 12:
                        # 每隔一分钟打印一次await
                        logger.debug('await worker %s %s %s', task_meta.task_key, worker.is_alive(), worker.ident)
                    worker.join(5)
                    if not worker.is_alive():
                        break
                    if self.is_done(): 
                        self._to_kill_workers.append(worker)
                        break
                logger.debug('end await worker %s, id=%s, exitcode=%s', task_meta.task_key, worker.ident, worker.exitcode)
            else:
                logger.debug('skip await worker %s, id=%s, exitcode=%s', task_meta.task_key, worker.ident, worker.exitcode)