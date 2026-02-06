from abc import abstractmethod
from smart.utils.path import url_path_join

class BaseStorageClient:
    def __init__(self, connection, **kwargs) -> None:
        self._conn_kwargs = connection

    def path_join(self, path_list):
        return url_path_join(*path_list)

    @abstractmethod
    def fget_object(self, bucket_name, object_name, file_path, **kwargs):
        raise 'Unsupport func: BaseStoreClient.fget_object'

