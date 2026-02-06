'''
python -m tests.auto_task.redis.run_redis_pip test_send --host 127.0.0.1 --port 6379
python -m tests.auto_task.redis.run_redis_pip test_send_timeout --host 127.0.0.1 --port 6379
python -m tests.auto_task.redis.run_redis_pip test_send_item --host 127.0.0.1 --port 6379
python -m tests.auto_task.redis.run_redis_pip test_recv --host 127.0.0.1 --port 6379
python -m tests.auto_task.redis.run_redis_pip test_send --use_cluster --host 'redis-node-0,redis-node-1,redis-node-2' --password=bitnami
python -m tests.auto_task.redis.run_redis_pip test_recv --use_cluster --host 'redis-node-0,redis-node-1,redis-node-2' --password=bitnami
'''
from smart.auto.run import auto_run

TEST_REDIS_KEY = 'tests:auto_tasks.redis.test'


def test_send(host='127.0.0.1', port=6379, key=None, password=None, db:int=0, use_cluster:bool=False, 
              send_end_cmd=True, queue_ttl:int=None):
    auto_run('auto_tasks.tasks', 
        name='task:tools__tool.range~@redis__pip.conn(redis_local)~@redis__pip.send(send_args)', 
        bind_arg={
            'redis__pip.send': {
                'key': key or TEST_REDIS_KEY,
                'send_end_cmd': send_end_cmd
            }
        }, 
        extra={
            'configs': {
                'redis_local': {
                    'host': host,
                    'port': port,
                    'password': password,
                    'db': db,
                    'use_cluster': use_cluster,
                    'redis_kwargs': {
                        'socket_timeout': 60,
                        'socket_connect_timeout': 60,
                    }
                },
                'send_args': {
                    'queue_ttl': queue_ttl
                }
            }
        })

def test_send_timeout(host='127.0.0.1', port=6379, key=None, password=None, db:int=0
        , client_timeout=10):
    auto_run('auto_tasks.tasks', 
        name='task:tools__tool.range(test_range)~@redis__pip.conn(redis_local)~@redis__pip.send(pip_sender)', 
        bind_arg={
            'redis__pip.send': {
                'key': key or TEST_REDIS_KEY
            }
        }, 
        extra={
            'configs': {
                'test_range': {
                    'size': 20
                },
                'redis_local': {
                    'host': host,
                    'port': port,
                    'password': password,
                    'db': db,
                },
                'pip_sender': {
                    'max_queue_size': 10,
                    'client_timeout': client_timeout,
                    'queue_ttl': 3600,
                }
            }
        })

def test_send_item(host='127.0.0.1', port=6379, key=None, password=None, db:int=0
        , client_timeout=10):
    auto_run('tests.auto_task.test', 
        name='task:test_redis_data.item_iter_fn(test_item_iter_args)~@redis__pip.conn(redis_local)~@redis__pip.send(pip_sender)', 
        bind_arg={
            'redis__pip.send': {
                'key': key or TEST_REDIS_KEY
            }
        }, 
        extra={
            'configs': {
                'test_item_iter_args': {
                    'num_items': 20
                },
                'redis_local': {
                    'host': host,
                    'port': port,
                    'password': password,
                    'db': db,
                },
                'pip_sender': {
                    'max_queue_size': 10,
                    'item_queue_key': '_resp_key',
                    'client_timeout': client_timeout,
                    'item_resp_ttl_key': '_resp_ttl',
                    'queue_ttl': 3600,
                }
            }
        })

def test_recv(host='127.0.0.1', port=6379, key=None, password=None, db:int=0, use_cluster:bool=False, 
              is_daemon=False, key_item_redis='_redis_key', timeout=10, redis_poll_interval=None):
    auto_run('auto_tasks.tasks', 
        name='task:redis__pip.conn(redis_local)~recv~@tools__print.item_iter', 
        bind_arg={
            'tools__print.item_iter': {
                'head': None
            },
            'redis__pip.recv': {
                'key': key or TEST_REDIS_KEY,
                'block': True,
                'timeout': timeout,
                'is_daemon': is_daemon,
                'key_item_redis': key_item_redis,
                'redis_poll_interval': redis_poll_interval,
            }
        }, 
        extra={
            'configs': {
                'redis_local': {
                    'host': host,
                    'port': port,
                    'password': password,
                    'db': db,
                    'use_cluster': use_cluster,
                    'redis_kwargs': {
                        'socket_timeout': 60,
                        'socket_connect_timeout': 60,
                    }
                }
            }
        })




if __name__ == "__main__":
    import fire
    
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })