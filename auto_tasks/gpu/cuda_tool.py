import os, time

from smart.auto import TreeMultiTask
from smart.utils.env import auto_set_env_by_prefix, AppEnv
from smart.utils.cast import cast_bool
from .__utils import auto_load, logger, task_hook
from .GpuTool import GpuInfoGetter, MemInfo


_options = {
    "nvml_is_disable": False
}

try:
    import pynvml
except:
    _options['nvml_is_disable'] = True
    _options['err_msg'] = "miss pynvml"


class CudaInfoGetter(GpuInfoGetter):
    def __init__(self) -> None:
        self.__inited = False
    
    def __nvmlInit(self):
        if not self.__inited:
            pynvml.nvmlInit()
            self.__inited = True

    def get_device_count(self):
        self.__nvmlInit()
        return pynvml.nvmlDeviceGetCount()
        
    def get_memory_info(self, index:int):
        self.__nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(index)
        meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return MemInfo(
            meminfo.total, meminfo.free, meminfo.used
        )


@auto_load.task('gpu_tools.cuda_tool')
class CudaToolTask(TreeMultiTask):
    def find_available_gpu(self, gpu_num:int=1, shuffle:bool=False,
            free_memory:int=None, free_memory_ratio:float=None, 
            device_env_key:str='CUDA_VISIBLE_DEVICES', ctx_state_name:str='cuda_tool'):
        """查找可用的GPU
        当free_memory和free_memory_ratio都为None时，所有显卡都为可用，返回的available_gpu数组长度=min(gpu_num, 机器实际显卡数)。
        shuffle=True可随机获取可用显卡；shuffle=False则按顺序检查可用显卡。
        查找可用显卡以执行代码的时刻的显存来判断，与实际占用显卡一般有一段间隔。
        在多个任务并发时，可能会出现多个任务同时在抢占同一张显卡。shuffle=True能减少抢占情况。

        Args:
            gpu_num (int, optional): 需要的GPU数量. Defaults to 1.
            shuffle (bool, optional): 是否随机打乱GPU顺序. Defaults to False.
            free_memory (int, optional): 显卡的可用显存小于free_memory为不可用. Defaults to None.
            free_memory_ratio (float, optional): 显卡的可用显存/显存小于free_memory_ratio为不可用. Defaults to None.
            device_env_key (str, optional): 将可用的设备序号设置到环境变量中, 空值表示不设置环境变量. Defaults to 'CUDA_VISIBLE_DEVICES'.
            ctx_state_name (str, optional): 将返回的available_gpu列表保存到context中. Defaults to 'cuda_tool'.

        Returns:
            dict: {"available_gpu":[(显卡序号:int, 显存信息:MemInfo)]}
        """
        if not cast_bool(AppEnv.get("USE_GPU", True)):
            return

        if _options['nvml_is_disable']:
            logger.error("nvml is not support. %s", _options.get("err_msg", ""))
            return

        cuda = CudaInfoGetter()

        with self.context.store.lock((ctx_state_name, "find_available_gpu")):
            used_gpu = self.context.list((ctx_state_name, "used_gpu"))
            used_gpu_idx = [idx for idx, _ in used_gpu]

            choosed_gpu = cuda.find_mem_free_device(
                gpu_num=gpu_num, 
                shuffle=shuffle,
                free_memory=free_memory, 
                free_memory_ratio=free_memory_ratio,
                filter_fn=lambda idx, _:(idx in used_gpu_idx)
            )

            if choosed_gpu:
                self.context.list((ctx_state_name, "used_gpu")).extend(choosed_gpu)
        
        if device_env_key:
            device_env_val = ','.join([
                str(val[0]) for val in choosed_gpu
            ])
            auto_set_env_by_prefix(device_env_key, device_env_val)
            logger.info("cuda_tool.find_available_gpu set_env %s: %s", device_env_key, device_env_val)

        return {
            "available_gpu": choosed_gpu
        }
    
    @task_hook.before_task()
    def hook_available_gpu(self, gpu_num:int=1, shuffle:bool=False,
            free_memory:int=None, free_memory_ratio:float=None, 
            device_env_key:str=None, ctx_state_name:str='cuda_tool'):
        """查找可用的GPU的勾子函数(在其他任务启动前先执行)
        当free_memory和free_memory_ratio都为None时，所有显卡都为可用，返回的available_gpu数组长度=min(gpu_num, 机器实际显卡数)。
        shuffle=True可随机获取可用显卡；shuffle=False则按顺序检查可用显卡。
        查找可用显卡以执行代码的时刻的显存来判断，与实际占用显卡一般有一段间隔。
        在多个任务并发时，可能会出现多个任务同时在抢占同一张显卡。shuffle=True能减少抢占情况。

        Args:
            gpu_num (int, optional): 需要的GPU数量. Defaults to 1.
            shuffle (bool, optional): 是否随机打乱GPU顺序. Defaults to False.
            free_memory (int, optional): 显卡的可用显存小于free_memory为不可用. Defaults to None.
            free_memory_ratio (float, optional): 显卡的可用显存/显存小于free_memory_ratio为不可用. Defaults to None.
            device_env_key (str, optional): 将可用的设备序号设置到环境变量中, 空值表示不设置环境变量. Defaults to None.
            ctx_state_name (str, optional): 将返回的available_gpu列表保存到context中. Defaults to 'cuda_tool'.

        Returns:
            dict: {"available_gpu":[(显卡序号:int, 显存信息:MemInfo)]}
        """
        if not cast_bool(AppEnv.get("USE_GPU", True)):
            return
        if _options['nvml_is_disable']:
            logger.error("nvml is not support. %s", _options.get("err_msg", ""))
            return

        cuda = CudaInfoGetter()

        choosed_gpu = cuda.find_mem_free_device(
            gpu_num=gpu_num, 
            shuffle=shuffle,
            free_memory=free_memory, 
            free_memory_ratio=free_memory_ratio
        )

        if device_env_key:
            device_env_val = ','.join([
                str(val[0]) for val in choosed_gpu
            ])
            auto_set_env_by_prefix(device_env_key, device_env_val)
            logger.info("cuda_tool.hook_available_gpu set_env %s: %s", device_env_key, device_env_val)

        if ctx_state_name:
            self.context.state(ctx_state_name).update({
                "available_gpu_num": len(choosed_gpu),
                "available_gpu_list": choosed_gpu
            })

        return {
            "available_gpu": choosed_gpu
        }

    def pop_gpu_from_ctx(self, gpu_num:int=1, min_gpu_num:int=0, 
                device_env_key:str='CUDA_VISIBLE_DEVICES', ctx_state_name:str='cuda_tool'):
        """从context中获取可用GPU, 并将GPU序号保存到环境变量
        本方法与hook_available_gpu搭配使用. 
        当可用的GPU数量少于min_gpu_num时, 则不从context的available_gpu_list中pop数据, 同时CUDA_VISIBLE_DEVICES环境变量设置为-1. 

        Args:
            gpu_num (int, optional): 需要的gpu数量. Defaults to 1.
            min_gpu_num (int, optional): 最小需要的gpu数量. Defaults to 0.
            device_env_key (str, optional): 保存GPU序号的环境变量, 本参数一般不修改. Defaults to 'CUDA_VISIBLE_DEVICES'.
            ctx_state_name (str, optional): 保存可用GPU列表的context名称, 本参数一般不修改. Defaults to 'cuda_tool'.

        Returns:
            dict: {available_gpu:[(显卡序号:int, 显存信息:MemInfo)]}
        """
        if not cast_bool(AppEnv.get("USE_GPU", True)):
            return
            
        if gpu_num < min_gpu_num:
            gpu_num = min_gpu_num

        ctx_state = self.context.state(ctx_state_name)
        available_gpu_num = ctx_state.wait("available_gpu_num")
        choosed_gpu = []

        if available_gpu_num >= min_gpu_num:
            with self.context.store.lock((ctx_state_name, "pop_gpu_from_ctx")):
                gpu_list = ctx_state.get("available_gpu_list")
                logger.debug("CudaToolTask.pop_gpu_from_ctx current gpu_list=%s", gpu_list)
                # time.sleep(1)

                try:
                    if gpu_list and len(gpu_list) >= min_gpu_num:
                        for i in range(gpu_num):
                            gpu_idx_info_tuple = gpu_list.pop(0)
                            choosed_gpu.append(gpu_idx_info_tuple)
                except IndexError:
                    logger.info("CudaToolTask.pop_gpu_from_ctx no enough gpu")
                
                ctx_state.set("available_gpu_list", gpu_list)
        
        if device_env_key:
            os.environ[device_env_key] = ", ".join(
                str(i) for i, _ in choosed_gpu
            ) if len(choosed_gpu) else "-1"
            logger.info("CudaToolTask.pop_gpu_from_ctx set %s=%s", device_env_key, os.environ[device_env_key])
        
        return {
            "available_gpu": choosed_gpu
        }
    

