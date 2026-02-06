from smart.auto.tree import TreeMultiTask
from smart.auto.Runner import AutoRunner
from smart.auto.ctx.runner_context import WithAutoRunner

from .__utils import auto_load, logger


@auto_load.task('lib.auto')
class LibAuto(TreeMultiTask, WithAutoRunner):
    def run_tree(self, tree_name):
        auto_runner:AutoRunner = getattr(self, 'auto_runner', None)
        logger.debug('LibAuto.run_tree: %s', tree_name)

        if auto_runner:
            auto_runner.start(tree_name)
        else:
            logger.error('!!! lib.auto.run_tree fail because auto_runner is empty, maybe you should use lib.auto as task_cls')

    def run_task(self, task_exp):
        auto_runner:AutoRunner = getattr(self, 'auto_runner', None)
        logger.debug('LibAuto.run_task: %s', task_exp)

        if auto_runner:
            auto_runner.start(task_exp, default_ns='task')
        else:
            logger.error('!!! lib.auto.run_task fail because auto_runner is empty, maybe you should use lib.auto as task_cls')