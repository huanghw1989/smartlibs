import datetime
from smart.auto import TreeMultiTask, AutoLoad

auto_load = AutoLoad()


@auto_load.task("test_auto_task.test_redis_data")
class TestRedisDataTask(TreeMultiTask):
    def item_iter_fn(self, num_items:int=10):
        def _fn():
            for i in range(num_items):
                yield {
                    "i": i,
                    "_resp_ttl": 60,
                    "_resp_key": 'tests:auto_tasks.redis.test_items',
                    "ctime": datetime.datetime.now()
                }
        return {
            'item_iter': _fn(),
            'item_iter_fn': _fn
        }

