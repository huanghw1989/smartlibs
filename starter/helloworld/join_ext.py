"""Ch4. Task join ext function

TaskExp example: 
task:mock_dataset.@mock_dataset_cfgs.default_cfg~start~@debug_tools.print_ds_example

Cmd Example: 
python -m smart.auto.run starter.helloworld.auto task:mock_dataset.@mock_dataset_cfgs.default_cfg~start~@debug_tools.print_ds_example
"""
import numpy as np

from .utils import auto_load, logger
from smart.auto.tree import TreeMultiTask


@auto_load.task('mock_dataset_cfgs')
class MockDatasetConfigs(TreeMultiTask):
    @auto_load.method('mock_dataset_cfgs.default_cfg')
    def default_cfg(task):
        print('default_cfg', task)
        return {
            'num_items': 20,
            'hidd_size': 10
        }

@auto_load.func_task('mock_dataset')
def input_fn_builder(task, num_items = 10, hidd_size=5, vocab_size=20):
    vocab_table = np.random.normal(size=[vocab_size, hidd_size])
    vocab_labels = np.random.normal(size=[vocab_size, 1]) > 0
    vocab_labels.dtype = 'int8'
    logger.info('mock_dataset input_fn_builder %s', (num_items, hidd_size, vocab_size))
    def input_fn():
        logger.info('mock_dataset input_fn %s', (num_items, hidd_size, vocab_size))
        for i in range(num_items):
            yield {
                'id': i,
                'token': vocab_table[i % vocab_size],
                'label': vocab_labels[i % vocab_size],
                'group': 'abcdefghij'[i % 9:i % 9 + i % 5 + i % 3 + i % 2]
            }
    return {
        'input_fn': input_fn
    }

@auto_load.task('debug_tools')
class DebugTools(TreeMultiTask):
    def print_ds_example(task, input_fn, head=3):
        for i, item in enumerate(input_fn()):
            logger.info('dataset example %d: %s', i, item)