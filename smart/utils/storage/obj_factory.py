from .base import BaseStorageClient
from .obj_storage import ObjStorage
from .local_storage import LocalStorageClient
from smart.utils.config import SmartEnv
from smart.utils.loader import dyn_import


def create_client(type, connection, **kwargs):
    if type =='local':
        return LocalStorageClient(connection=connection, **kwargs)
    if type == 'minio':
        from .minio_storage import MinioClient
        return MinioClient(connection=connection, **kwargs)
    else:
        client_cls = dyn_import(type)
        if issubclass(client_cls, BaseStorageClient):
            return client_cls(connection=connection, **kwargs)
        raise Exception('unsupport StorageClient type={}'.format(str(type)))


class ObjStorageFactory:
    Default_Store_Type = 'local'

    def __init__(self, env:SmartEnv=None, root_env_path:tuple=None) -> None:
        self._store_instances = {}
        self._env = env
        self._root_env_path = root_env_path or ('app', 'obj_storage')
        self._connections_env_path = (*self._root_env_path, 'connections')

    def get_store(self, store_name, config:dict, cache_dir:str=None) -> ObjStorage:
        if store_name not in self._store_instances:
            self._store_instances[store_name] = self.create_obj_store_by_config(
                config=config,
                cache_dir=cache_dir
            )
        return self._store_instances[store_name]

    def get_store_by_env(self, store_name, cache_dir:str=None) -> ObjStorage:
        if store_name not in self._store_instances:
            config = self._env.get((*self._root_env_path, store_name)) or {}
            connection = None
            if 'connection' not in config:
                connection_name = config.get('connection_name')
                connection = self._env.get((*self._connections_env_path, connection_name))
            self._store_instances[store_name] = self.create_obj_store_by_config(
                config=config,
                connection=connection,
                cache_dir=cache_dir
            )
        return self._store_instances[store_name]

    def create_obj_store_by_config(self, config:dict, connection:dict=None, cache_dir:str=None):
        store_type = config.get('type') or ObjStorageFactory.Default_Store_Type
        conn_kwargs = connection or config.get('connection')
        bucket_name = config.get('bucket_name')
        bucket_root_path = config.get('bucket_root_path')
        cache_dir = cache_dir or config.get('cache_dir')

        assert conn_kwargs and bucket_name

        client = create_client(
            type=store_type,
            connection=conn_kwargs
        )
        store = ObjStorage(
            client=client,
            cache_dir=cache_dir,
            bucket_name=bucket_name,
            bucket_root_path=bucket_root_path
        )
        return store