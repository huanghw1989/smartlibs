import os, time, queue, asyncio, inspect, signal
import multiprocessing as mp
import threading

from smart.utils.number import safe_parse_int

from smart.rest.__logger import logger_rest


class BaseTaskManager:
    def __init__(self):
        self.end_flag = False


class TimingTask:
    MIN_INTERVAL = .1

    def __init__(self, interval, task_func, task_args, task_kwargs, rst_queue:queue.Queue=None, opts = {}):
        self.interval = max(interval, 1)
        self.task_func = task_func
        self.task_args = task_args
        self.task_kwargs = task_kwargs
        self.rst_queue = rst_queue
        self.opts = opts
    
    async def __exec_task(self):
        rst, err = None, None
        task_func = self.task_func

        try:

            if inspect.iscoroutinefunction(task_func):
                rst = await task_func(*self.task_args, **self.task_kwargs)
            else:
                rst = task_func(*self.task_args, **self.task_kwargs)
        except BaseException as e:

            err = e
            logger_rest.exception('TimingTask.__exec_task err: %s', e)
        except KeyboardInterrupt as e:

            raise e

        if self.rst_queue is not None:
            self.rst_queue.put((self, rst, err))

        return rst, err
    
    async def sleep(self, interval, manager:BaseTaskManager):
        if manager and manager.end_flag:
            return
        
        # logger_rest.debug('TimingTask %s sleep %s second', self.task_func, interval)
        while interval:
            if manager.end_flag:
                raise KeyboardInterrupt('end_flag')

            if interval > 3:
                interval -= 3
                await asyncio.sleep(3)
            else:
                await asyncio.sleep(interval)

    async def start_loop(self, manager:BaseTaskManager):
        logger_rest.debug('TimingTask %s start_loop interval=%s', self.task_func, self.interval)

        try:

            run_immediate = self.opts.get('run_immediate', False)

            if not run_immediate:
                await self.sleep(self.interval, manager)

            while not (manager and manager.end_flag):
                start_ts = time.time()

                rst, err = await self.__exec_task()

                end_ts = time.time()
                delay = max(self.MIN_INTERVAL, self.interval-end_ts+start_ts)

                await self.sleep(delay, manager)
            
            logger_rest.debug('TimingTask end loop: %s', self.task_func)

        except KeyboardInterrupt:
            # logger_rest.debug('TimingTask end loop(KeyboardInterrupt): %s', self.task_func)
            pass


class TimingTaskMeta:
    def __init__(self, timing_fn, interval:int, timing_fn_args=[], timing_fn_kwargs={}, run_immediate=False):
        self.timing_fn = timing_fn
        self.timing_fn_args = timing_fn_args or []
        self.timing_fn_kwargs = timing_fn_kwargs or {}
        self.__interval = interval
        self.run_immediate = run_immediate
    
    @property
    def interval(self):
        interval = self.__interval

        if callable(interval):
            interval = interval()
        
        return max(safe_parse_int(interval), 1)


class Crond(BaseTaskManager):
    schedule_tasks = []
    timing_tasks = mp.Queue()

    def __init__(self):
        BaseTaskManager.__init__(self)

        self.run_timing_tasks = []
        self.status = 'inited'
        self.main_process = None
        self.main_thread = None
        self.event_loop = None
        self.loop_task = None
        self.async_tasks = None
        
    @staticmethod
    def add_timing_task(task:TimingTaskMeta):
        Crond.timing_tasks.put(task)

    def run(self): 
        self.status = 'start'

        while True:
            try:
                task_meta:TimingTaskMeta = self.timing_tasks.get(block=True, timeout=1)

                task = TimingTask(
                    interval = task_meta.interval,
                    task_func = task_meta.timing_fn,
                    task_args = task_meta.timing_fn_args,
                    task_kwargs = task_meta.timing_fn_kwargs,
                    opts = {
                        'run_immediate': task_meta.run_immediate
                    }
                )
                self.run_timing_tasks.append(task)
            except queue.Empty:
                break

        if not len(self.run_timing_tasks):
            logger_rest.info('no cron task, exit crond')
            self.status = 'exit'
            return
        elif self.end_flag:
            logger_rest.info('crond exit(end_flag)')
            self.status = 'exit'
            return

        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            self.event_loop = loop
            self.async_tasks = [
                loop.create_task(task.start_loop(manager=self))
                for task in self.run_timing_tasks
            ]
            
            self.loop_task = loop.run_until_complete(asyncio.wait(
                self.async_tasks
            ))
        except KeyboardInterrupt:
            logger_rest.info('crond exit(KeyboardInterrupt)')
        else:
            logger_rest.info('crond exit')
        finally:
            loop.close()
            self.status = 'exit'

    def daemon(self, run_in_process=False, run_in_thread=False) -> mp.Process:
        if run_in_process:

            logger_rest.info('Crond run_in_process')
            self.main_process = main_process = mp.Process(target=self.run)
            main_process.start()

            return main_process
        elif run_in_thread:

            logger_rest.info('Crond run_in_thread')
            self.main_thread = main_thread = threading.Thread(target=self.run)
            main_thread.start()

            return main_thread
        else:
            
            logger_rest.info('Crond run')
            self.run()
    
    def close(self):
        if self.main_process:
            
            pid = self.main_process.pid
            logger_rest.debug('crond(pid=%s) closing', pid)

            os.kill(pid, signal.SIGINT)
            self.main_process.join()

            logger_rest.debug('crond closed')
        else:

            logger_rest.debug('crond closing')
            self.end_flag = True

            # if self.async_tasks:
            #     for task in self.async_tasks:
            #         task.cancel()

            # if self.event_loop:
            #     loop = self.event_loop
            #     # all_tasks = asyncio.Task.all_tasks()

            #     # for task in self.async_tasks:
            #     #     task.cancel()
                    
            #     try:
            #         loop.stop()
            #         loop.run_forever()
            #     except Exception as e:
            #         logger_rest.warning('Crond event_loop fail close %s', e)
            #     finally:
            #         loop.close()


