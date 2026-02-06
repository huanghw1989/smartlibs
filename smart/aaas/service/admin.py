from smart.utils import AppEnv

from smart.rest import RestRoute, RestService, RequestException

from smart.aaas.base import AaasErrorCode

from smart.aaas.__logger import logger
import pynvml
import os


rest = RestRoute()


@rest.service('/admin')
class AdminService(RestService):
    @rest.get('shut_down')
    def shut_down(self):
        sig = getattr(self.app, '__sig_shut__', None)

        logger.info('Shut down aaas by client ip=%s', self.request.client_address)

        if sig:
            sig.put('shut_down_app')
        else:
            raise RequestException("shut_down is disable, you should enable it by smart_aaas --shuttable", AaasErrorCode.default)

        return 1


    @rest.get('gpu_stat')
    def gpu_stat(self):
        if os.sep == '/':
            free_gpu_list = self.get_free_gpu_list()
        else:
            free_gpu_list = []
        return free_gpu_list
        

    def gpu_is_free(self, gpu_id):
        '''根据显存使用量判断gpu空闲状态
        '''
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id) # 0表示第一块显卡
        meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
        if meminfo.free/meminfo.total > 0.95:
            return True
        return False

    def get_free_gpu_list(self):
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        free_gpu_list = []
        
        for i in range(gpu_count):

            if self.gpu_is_free(i):
                free_gpu_list.append(i)
        return free_gpu_list

