from .base import BaseStorageClient
from minio import Minio


class MinioClient(BaseStorageClient):
    def __init__(self, connection, **kwargs) -> None:
        super().__init__(connection=connection, **kwargs)
        self._minio = Minio(**connection)

    def fget_object(self, bucket_name, object_name, 
                    file_path, **kwargs):
        return self._minio.fget_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=file_path,
            **kwargs
        )