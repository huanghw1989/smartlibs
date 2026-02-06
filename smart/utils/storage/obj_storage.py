import os
from smart.utils.path import path_join
from .base import BaseStorageClient


class ObjStorage:
    def __init__(self, client:BaseStorageClient, cache_dir, bucket_name, bucket_root_path='') -> None:
        self._client = client
        self._cache_dir = cache_dir
        self._bucket_name = bucket_name
        self._bucket_root_path = bucket_root_path
        self._last_fget_result = None
    
    def fget(self, obj_file_path:str, use_cache=True, local_file_path=None, **kwargs):
        """从对象存储上转存文件到本地

        Args:
            obj_file_path (str): 对象地址
            use_cache (bool, optional): 是否使用本地缓存的文件；false会始终从对象存储下载. Defaults to True.
            local_file_path (str, optional): 转存到本地文件地址. Defaults to None, 自动拼接缓存目录和对象地址作为本地文件路径.

        Returns:
            str: 转存后的本地文件地址
        """
        if not obj_file_path:
            return None
        obj_file_path = obj_file_path.lstrip('/')
        if not local_file_path:
            local_file_path = path_join(self._cache_dir, obj_file_path, auto_mkdir=True)
        if use_cache and os.path.exists(local_file_path):
            return local_file_path
        obj_path = self._client.path_join([self._bucket_root_path, obj_file_path])
        fget_result = self._client.fget_object(
            bucket_name=self._bucket_name,
            object_name=obj_path,
            file_path=local_file_path, 
            **kwargs
        )
        self._last_fget_result = fget_result
        return local_file_path
