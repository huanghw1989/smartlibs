import uuid, time, functools, os, signal
import multiprocessing as mp
from multiprocessing.context import TimeoutError
from queue import Empty
import traceback

from smart.utils import AppEnv
from smart.utils.store.mp_store import MpContextStore
from smart.utils.process import on_process_init
from smart.utils.number import safe_parse_int
from smart.utils.dict import dict_get_or_set
# from smart.utils.log import auto_load_logging_config, set_default_logging_config

from smart.rest import cron_timing

from smart.auto.run import auto_run

from smart.aaas.base import AutoTaskDoneFlag
from smart.aaas.process_pool import Pool
from smart.aaas.state.state_hook import get_hook, report_state
from smart.aaas.__logger import logger
from smart.aaas.task_log import TaskFileLog


class AutoManage:
    DEBUG_CLEAN = False
    all_instances = set()

    def __init__(self):
        self.__inited = False
        self.store = None
        self._jobs = None
        self.main_process = None
        self.mp_pool = None
        self.worker_num = None
    
    def task_uuid(self):
        """Generate Task UUID
        
        Returns:
            str -- uuid
        """
        return uuid.uuid1().hex

    def call_auto_run(self, module, name, run_opts, task_id=None, task_ns=None):
        """call smart.auto.run.auto_run function, update task_info dict before and after calling if task_id is not None

        Only Parse Task shound pass empty task_id
        
        Arguments:
            module {str} -- dotted module path
            name {str} -- tree name or task expression(with namspace prefix 'task:')
            run_opts {dict} -- auto_run fn kwargs
        
        Keyword Arguments:
            task_id {str} -- Task UUID
            task_ns {str} -- Task Namespace
        """
        on_process_init()
        
        task_log, resp = None, {}

        def __before_run():
            if task_id is not None:
                delay = safe_parse_int((run_opts or {}).pop('delay', 0), 0)

                task_dict = self.get_task_dict(task_ns)
                task_info = task_dict.get(task_id)

                with self.store.lock('task_info'):
                    task_info = task_dict.get(task_id)

                    if task_info is not None:
                        if task_info.get('end_flag'):
                            resp['done_flag'] = AutoTaskDoneFlag.end_flag.flag_value

                            logger.info('skip call_auto_run by end flag: %s', task_info)

                            return resp

                        process_info = task_info.get('process')

                        if process_info is None:
                            task_info['process'] = process_info = {}
                        else:
                            logger.warning('duplicate call_auto_run: %s', task_info)
                            return resp
                        
                        process_info.update({
                            'pid': os.getpid(),
                            'ppid': os.getppid()
                        })
                        if task_log:
                            task_info['task_log'] = task_log.task_info()
                        stage_list = dict_get_or_set(task_info, ('stage'), [])
                        stage_list.append('start')
                        task_dict[task_id] = task_info
                
                if delay > 0:
                    logger.debug('delay task %s %d seconds', (task_id, task_ns), delay)
                    time.sleep(delay)
                
                return task_info

        try:
            task_log = TaskFileLog(task_id=task_id, task_ns=task_ns)

            if self.__end_flag():
                resp['done_flag'] = AutoTaskDoneFlag.interrupt.flag_value
                logger.info('task %s skip because of end_flag', task_id)
                return resp

            task_info = __before_run() or {}

            try:
                # 任务状态上报
                state_hook = task_info.get('state_hook')
                report_state(state_hook, task_id, "start", task_info, auto_close=True)
                # 运行任务
                rst = auto_run(module, name, **run_opts)
                resp['result'] = rst
            except KeyboardInterrupt:
                
                raise KeyboardInterrupt()
            except BaseException as e:

                logger.exception(e)
                resp['error'] = e
                resp['error_traceback'] = traceback.format_exc()
        except KeyboardInterrupt:

            resp['done_flag'] = AutoTaskDoneFlag.interrupt.flag_value
            logger.info('task %s end (KeyboardInterrupt)', task_id)
        
        finally:
            if task_log:
                task_log.close(reset_logger=True)

        return resp
    
    def __end_flag(self):
        return self.store.value('end_flag').get(False)
    
    def _backend_job(self, jobs:mp.Queue=None):
        """backend job dispatcher
        """
        on_process_init()

        jobs = jobs or self._jobs

        # 这两个个变量无法被pickle.dumps, 后台进程也用不到它们，所以设置为None
        self._jobs, self.main_process = None, None
            
        pool_kwargs = {
            'processes': self.worker_num,
            'maxtasksperchild': 1
        }
        self.mp_pool = Pool(**pool_kwargs)
        logger.debug('Auto Task Pool Options: %s', pool_kwargs)
        
        try:
            while not self.__end_flag():
                try:
                    fn_name, fn_kwargs = jobs.get(block=True, timeout=3)

                    if fn_name == 'break':
                        break
                    elif fn_kwargs is None:
                        fn_kwargs = {}

                    getattr(self, fn_name)(**fn_kwargs)
                except Empty:
                    continue
                except KeyboardInterrupt:
                    break
        finally:
            self.mp_pool.close()
            self.mp_pool.join()
            logger.debug('auto manage backend_job exit')
    
    def _init(self):
        """call in main process
        """
        if not self.__inited:
            self.__inited = True
            self.store = MpContextStore()
            # self._jobs = mp.Queue()
            self._jobs = self.store.manager.Queue()
            self.main_process = mp.Process(
                target=self._backend_job, 
                args=(self._jobs, )
            )
            self.worker_num = int(AppEnv.get('AUTO_WORKER_NUM', 2))
            self.all_instances.add(self)

            # spawn进程模式下, call_auto_run进程新建的store再次使用时报错
            # 临时修复方案: 预创建 call_auto_run 需要用的store
            self.store.lock('task_info')
    
    def start(self):
        """call in main process
        """
        self._init()
        
        self.main_process.start()
        logger.info('AutoManage started pid=%s', self.main_process.pid)
        
        return self.main_process
    
    def _create_task_cb(self, event, task_ns_id, task_result):
        logger.info("task callback-%s %s %s", event, task_ns_id, task_result)

        task_ns, task_id = task_ns_id
        rst_err, rst, err_traceback = None, None, None
        task_result = task_result or {}

        if event == 'error' and isinstance(task_result, Exception):
            # logger.exception(task_result)
            err_traceback = traceback.format_exc()
            logger.error(err_traceback)
            rst_err = task_result
            task_result = {}
        else:
            rst = task_result.get('result')
            rst_err = task_result.get('error')
            err_traceback = task_result.get('error_traceback')
        
        task_dict = self.get_task_dict(task_ns)
        task_info = task_dict.get(task_id)

        if not task_info:
            logger.warning("task %s missing task_info", task_ns_id)
            return

        task_info['done_time'] = time.time()
        task_info['done_flag'] = task_result.get('done_flag', AutoTaskDoneFlag.done.flag_value)
        
        if rst_err:
            task_info['exception'] = {
                'type': type(rst_err).__name__,
                'info': rst_err.args,
                'traceback': err_traceback
            }
        
        if rst is not None:
            task_info['task_resp'] = rst
        
        stage_list = dict_get_or_set(task_info, ('stage'), [])
        stage_list.append('end')
        task_dict[task_id] = task_info
        # 任务状态上报
        try:
            state_hook = task_info.get('state_hook')
            report_state(state_hook, task_id, event, task_info, auto_close=True)
        except Exception as e:
            logger.warning("state_hook error: %s", e)
    
    def _create_task(self, task_id, task_ns, module, name, run_opts, **kwargs):
        """backend job
        """
        pool = self.mp_pool

        pool_result = pool.apply_async(
            self.call_auto_run, 
            args = (module, name, run_opts, task_id, task_ns), 
            callback = functools.partial(self._create_task_cb, 'done', (task_ns, task_id)), 
            error_callback = functools.partial(self._create_task_cb, 'error', (task_ns, task_id))
        )

        try:
            run_result = pool_result.get(timeout=0)
            logger.info('aaas.auto_run %s: %s %s %s, rst=%s', 
                task_id, module, name, run_opts, run_result)
        except TimeoutError:
            logger.info('aaas.auto_run %s %s: %s %s %s', 
                task_id, 'done' if pool_result.ready() else 'starting',
                module, name, run_opts)
        except Exception as run_err:
            logger.error("_create_task error: %s", run_err)

    def create_task(self, task_id, task_ns, module, name, run_opts, state_hook=None):
        """call in any process
        
        Arguments:
            task_id {str} -- Task UUID
            task_ns {str} -- Task Namespace
            module {str} -- dotted module path
            name {str} -- tree name or task expression(with namspace prefix 'task:')
            run_opts {dict} -- auto_run fn kwargs
        
        Returns:
            dict -- task info {task_id, task_ns, module, name, run_opts, create_time, end_flag, process, done_flag, done_time}
        """
        if not task_id:
            task_id = self.task_uuid()

        task_dict = self.get_task_dict(task_ns)
        task_info = task_dict.get(task_id)

        if task_info is not None:
            return task_info
        
        with self.store.lock((task_ns or '', 'task_dict')):
            task_info = task_dict.get(task_id)

            if task_info is not None:
                return task_info
            
            task_info = {
                'task_id': task_id,
                'task_ns': task_ns,
                'module': module,
                'name': name,
                'run_opts': run_opts,
                'create_time': time.time(),
            }
            if state_hook:
                task_info['state_hook'] = state_hook
            task_dict[task_id] = task_info

        self._jobs.put(('_create_task', task_info))

        return task_info

    def get_task_dict(self, namespace):
        return self.store.dict(('task_dict', namespace or ''))
    
    def all_task_ns(self):
        for store_key in self.store.get_names('dict'):
            if isinstance(store_key, tuple) and len(store_key) == 2 and store_key[0] == 'task_dict':
                yield store_key[1]
    
    def clean_task_dict(self, task_ns, task_info_ttl:int):
        task_dict = self.get_task_dict(task_ns)
        clean_task_ids = []

        expire_ts = time.time() - task_info_ttl

        for task_id, task_info in task_dict.items():
            if not task_info:
                clean_task_ids.append(task_id)

            if task_info.get('done_flag'):
                done_time = task_info.get('done_time')
                if done_time and done_time > expire_ts:
                    # in ttl
                    continue
                clean_task_ids.append(task_id)
        
        if len(clean_task_ids):
            with self.store.lock((task_ns or '', 'task_dict')):
                task_dict = self.get_task_dict(task_ns)
                for task_id in clean_task_ids:
                    try:
                        del task_dict[task_id]
                    except KeyError:
                        pass
            
            logger.info('AutoManage.clean_task_dict ns=%s, ids=%s', task_ns, clean_task_ids)
        
        return clean_task_ids
    
    def get_task_info(self, task_id, namespace=None):
        """Get task info
        
        Arguments:
            task_id {str} -- Task UUID
        
        Keyword Arguments:
            namespace {str} -- Task Namespace (default: {None})
        
        Returns:
            dict -- task info {task_id, task_ns, module, name, run_opts, create_time, end_flag, process, done_flag, done_time}
        """
        tasks = self.get_task_dict(namespace)

        return tasks.get(task_id, {})
    
    def flag_end_if_no_start(self, task_dict, task_id):
        """Mark end_flag in the task_info dict if the task is not started
        
        Arguments:
            task_dict {dict} -- {task_id : task_info}
            task_id {str} -- task_id
        
        Returns:
            bool -- Whether to mark end_flag in the task_info
        """
        with self.store.lock('task_info'):
            task_info = task_dict.get(task_id)

            if task_info is None:
                return False
            
            process_info = task_info.get('process')

            if not process_info:
                task_info['end_flag'] = 1
                task_dict[task_id] = task_info

                return True

        return False
    
    def end_all_ns_task(self, task_ns):
        task_dict = self.get_task_dict(task_ns)
        
        if task_dict:
            for task_id in list(task_dict.keys()):
                self.end_task(task_dict, task_id)
        
        logger.debug('end all task in namespace %s', task_ns)
    
    def end_task(self, task_dict, task_id):
        if not task_dict:
            return 0

        task_info = task_dict.get(task_id)

        if not task_info:
            return 0
        
        if task_info.get('done_flag'):
            return 1
        
        process_info = task_info.get('process')

        if process_info is None:
            if self.auto_manage.flag_end_if_no_start(task_dict, task_id):
                return 1

        pid = process_info.get('pid')

        if AppEnv.get('DEBUG_KILL_TASK'):
            from smart.utils.remote_debug import enable_remote_debug
            enable_remote_debug()

        if pid:
            os.kill(pid, signal.SIGINT)
            logger.info('end_task kill pid %s, task: %s', pid, (task_id, task_info.get('module'), task_info.get('name')))

        return 2

    def __getstate__(self):
        """spawn 模式的多进程会使用 pickle 序列化本实例, 但mp_pool和self._jobs 不是 pickable 对象, 需排除
        """
        _dict = self.__dict__.copy()
        _dict.update(
            mp_pool=None,
            # main_process=None,
            _jobs=None
        )
        return _dict

    def __setstate__(self, state):
        """pickle 反序列化
        """
        self.__dict__.update(state)
    
    def close(self):
        logger.debug('auto manage closing')

        try:
            # all_instances 用于 __clean_task
            self.all_instances.remove(self)
        except KeyError:
            pass
        
        if self.__inited:
            self.store.value('end_flag').set(True)
            self._jobs.put(('break', None))

            all_namespace = list(self.all_task_ns())

            for i in range(2):
                if i:
                    time.sleep(.5)
                
                logger.debug('auto_manage end all task round %d, namespaces=%s', i, all_namespace)
                for task_ns in all_namespace:
                    self.end_all_ns_task(task_ns)

            main_process = self.main_process
            main_process.join()
                
            if self.store:
                self.store.close()

            logger.debug('auto manage closed')


def __clean_task_timing_fn(): 
    return max(safe_parse_int(AppEnv.get('auto_m_clean_timing', 300)), 5)


@cron_timing(__clean_task_timing_fn)
def __clean_task():
    OPT_TASK_INFO_TTL = max(safe_parse_int(AppEnv.get('auto_m_task_info_ttl', 86400)), 5)

    logger.debug('auto manage clean timing start, task info ttl=%d', OPT_TASK_INFO_TTL)

    for auto_m in AutoManage.all_instances:
        auto_m:AutoManage
        for task_ns in auto_m.all_task_ns():
            auto_m.clean_task_dict(task_ns, OPT_TASK_INFO_TTL)