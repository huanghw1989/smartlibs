import os, shutil
from smart.utils.dict import dict_find
from smart.utils.path import path_join
from smart.utils.env import env_eval_str
from .base import BaseStorageClient


class LocalStorageClient(BaseStorageClient):
    Default_Root_Dir = './logs'

    def __init__(self, connection, **kwargs) -> None:
        super().__init__(connection=connection, **kwargs)

    def path_join(self, path_list):
        return path_join(*path_list)
    
    def get_bucket_dir(self, bucket_name, auto_mkdir:bool=False):
        bucket_dir = dict_find(self._conn_kwargs, ('bucket_dir_mapping', bucket_name))
        if bucket_dir is None:
            bucket_dir = path_join(
                dict_find(self._conn_kwargs, ('root_dir',), self.Default_Root_Dir),
                bucket_name,
                auto_mkdir=auto_mkdir
            )
        bucket_dir = env_eval_str(bucket_dir)
        return bucket_dir

    def fget_object(self, bucket_name, object_name, file_path, **kwargs):
        dir_path = self.get_bucket_dir(bucket_name)
        obj_file_path = path_join(dir_path, object_name)

        if not os.path.exists(obj_file_path):
            raise FileNotFoundError(obj_file_path)
        
        obj_abs_path = os.path.abspath(obj_file_path)
        target_abs_path = os.path.abspath(file_path)

        copy_result = None
        if obj_abs_path != target_abs_path:
            copy_result = shutil.copyfile(
                src=obj_abs_path,
                dst=target_abs_path
            )

        return {
            'obj_file_path': obj_file_path,
            'copy_result': copy_result
        }