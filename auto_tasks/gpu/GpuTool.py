from .__utils import logger
from collections import namedtuple
import random


MemInfo = namedtuple('MemInfo', ['total', 'free', 'used'])


class GpuInfoGetter:
    def get_device_count(self) -> int:
        """获取显卡数量

        Returns:
            int: 显卡数量
        """
        pass

    def get_memory_info(self, index:int) -> MemInfo:
        """获取指定显卡的显存信息

        Args:
            index (int): 显卡序号, 0表示第一块显卡

        Returns:
            MemInfo: 显存信息
        """
        pass

    def find_mem_free_device(self, gpu_num:int=1, shuffle:bool=False,
                free_memory:int=None, free_memory_ratio:float=None, filter_fn:callable=None)->list:
        """查找显存足够的显卡列表
        free_memory和free_memory_ratio都为None时, 所有显卡都可返回。
        shuffle=True可随机获取可用显卡；shuffle=False则按顺序检查可用显卡。
        查找可用显卡以执行代码的时刻的显存来判断，与实际占用显卡一般有一段间隔。
        在多个任务并发时，可能会出现多个任务同时在抢占同一张显卡。shuffle=True能减少抢占情况。

        Args:
            gpu_num (int, optional): 需要查找的设备数量. Defaults to 1.
            shuffle (bool, optional): 是否随机打乱GPU获取顺序. Defaults to False.
            free_memory (int, optional): 过滤可用显存小于free_memory的显卡. Defaults to None.
            free_memory_ratio (float, optional): 过滤可用显存/显存小于free_memory_ratio的显卡. Defaults to None.
            filter_fn (callable, optional): 过滤可用显卡的函数, 例如lambda idx, memInfo:True将过滤所有显卡. Defaults to None.

        Returns:
            list: 数据结构为[tuple(显卡序号:int, 显存信息:MemInfo)]
        """
        gpu_count = self.get_device_count()
        gpu_index_iter = range(gpu_count)

        if shuffle:
            gpu_index_iter = list(gpu_index_iter)
            random.shuffle(gpu_index_iter)

        choosed_gpu = []

        for gpu_index in gpu_index_iter:
            meminfo:MemInfo = self.get_memory_info(gpu_index)

            _choose = True
            try:
                if free_memory_ratio is not None:
                    _ratio = float(meminfo.free) / meminfo.total
                    if _ratio < free_memory_ratio:
                        _choose = False
                
                if free_memory is not None:
                    if meminfo.free < free_memory:
                        _choose = False
                
                if filter_fn and filter_fn(gpu_index, meminfo):
                    _choose = False
            except Exception as err:
                logger.warning("find_mem_free_device err: %s", err)
                _choose = False
            
            if _choose:
                choosed_gpu.append((gpu_index, meminfo))
            
            if len(choosed_gpu) >= gpu_num:
                break
        
        return choosed_gpu