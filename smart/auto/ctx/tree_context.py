from smart.auto.base import BaseContext
from smart.auto.meta import TreeRunMode
from smart.utils.store.store import ContextStore
from smart.utils.store.mp_store import MpContextStore

from smart.auto.__logger import logger_trace, logger


class TreeContext(BaseContext):
    def __init__(self, configs={}):
        super().__init__(configs=configs)
        self.run_mode = None
        self.run_stage = None
        self.__store = None
    
    @property
    def store(self):
        if self.__store is None:
            if self.run_mode in (TreeRunMode.default, TreeRunMode.worker_mt):
                self.__store = ContextStore()
            else:
                self.__store = MpContextStore()
        
        return self.__store
    
    def state(self, name):
        return self.store.state(name)
    
    def list(self, name):
        return self.store.list(name)
    
    def close(self):
        if self.__store is not None:
            self.__store.close()
            logger_trace.debug('TreeContext store closed')
    
    def response(self):
        state = self.store.state('__resp__')
        
        if self.run_stage not in ('before_task', ):
            state.set_readonly()

        return state
    
    # def stop_task(self):
    #     if self.run_stage not in ('before_task', ):
    #         logger.warning('context.stop_task must be called in before_task hook')
    #     else:
    #         self.store.dict('__state__')['stop_task'] = 1
    #         logger.debug('context.stop_task')

    def stop_task(self, task_key=None, end_all=False):
        """标记停止任务 (仅能在 before_task 勾子函数中调用)

        Keyword Arguments:
            task_key {str} -- 标记停止任务单元的key (default: {None})
            end_all {bool} -- 标记停止任务树; True时将忽略task_key (default: {False})
        """
        if end_all:
            flag_name = 'stop_tree'
        elif task_key:
            flag_name = ('stop_task', task_key)
        else:
            logger.warning('context.stop_task fail because both task_key and end_all are empty')
            return

        if self.run_stage not in ('before_task', ):
            logger.warning('context.stop_task must be called in before_task hook')
        else:
            self.store.dict('__state__')[flag_name] = True
            logger.info('# context.stop_task %s', '__all__' if end_all else task_key)
    
    def is_stop_task(self, task_key=None, end_all=False):
        """任务是否被停止

        Keyword Arguments:
            task_key {str} -- 查询指定任务单元是否被标记停止 (default: {None})
            end_all {bool} -- 查询任务树是否被标记停止 (default: {False})

        Returns:
            bool -- 指定任务单元 / 任务树 是否被标记停止
        """
        end_flags = []
        
        if task_key:
            end_flags.append(('stop_task', task_key))

        if end_all:
            end_flags.append('stop_tree')

        for end_flag in end_flags:
            if self.store.dict('__state__').get(end_flag, False):
                return True
                
        return False
