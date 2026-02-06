import os, random, time

from smart.utils.env import auto_set_env_by_prefix
from auto_tasks.gpu.GpuTool import MemInfo
from ..__init__ import TreeMultiTask, auto_load, logger


@auto_load.task("test_cuda_tool")
class TestCudaToolTask(TreeMultiTask):
    @auto_load.hook.before_task()
    def mock_available_gpu(self, gpu_num:int=1, shuffle:bool=False,
            free_memory:int=None, free_memory_ratio:float=None, 
            device_env_key:str=None, ctx_state_name:str='cuda_tool'):

        available_gpu = [
            (0, MemInfo(25396838400, 20696072192, 4700766208)),
            (2, MemInfo(25396838400, 25393692672, 3145728)),
            (3, MemInfo(25396838400, 25393692672, 3145728)),
            (4, MemInfo(25396838400, 23404544000, 1992294400)),
            (5, MemInfo(25396838400, 21415395328, 3981443072))
        ]

        if shuffle:
            random.shuffle(available_gpu)

        if free_memory_ratio:
            available_gpu = list(filter(
                lambda x: float(x[1].free)/x[1].total >= free_memory_ratio,
                iter(available_gpu)
            ))
        
        if free_memory:
            available_gpu = list(filter(
                lambda x: x[1].free >= free_memory,
                iter(available_gpu)
            ))
        
        choosed_gpu = available_gpu[:gpu_num]

        if device_env_key:
            device_env_val = ','.join([
                str(val[0]) for val in choosed_gpu
            ])
            auto_set_env_by_prefix(device_env_key, device_env_val)
        
        self.context.state("cuda_tool").set(
            "available_gpu_num", len(choosed_gpu)
        )

        if ctx_state_name:
            self.context.state(ctx_state_name).update({
                "available_gpu_num": len(choosed_gpu),
                "available_gpu_list": choosed_gpu
            })

        return {
            "available_gpu": choosed_gpu
        }

    def model_a_predict(self):
        logger.info("model_a_predict use CUDA_VISIBLE_DEVICES=%s", os.environ['CUDA_VISIBLE_DEVICES'])

        for i, item in enumerate(self.recv_data()):
            data = {
                "idx_a": i,
                "text": str(item),
                "ts_a": time.time()
            }
            self.send_data(data)
            time.sleep(random.random())

    def model_b_predict(self):
        logger.info("model_b_predict use CUDA_VISIBLE_DEVICES=%s", os.environ['CUDA_VISIBLE_DEVICES'])
        
        for i, item in enumerate(self.recv_data()):
            item.update({
                "idx_b": i,
                "ts_b": time.time(),
            })
            self.send_data(item)