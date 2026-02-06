from smart.auto.tree import TreeMultiTask
from smart.aaas.client import AaasClient
from smart.utils.yaml import yaml_dumps

from .__utils import auto_load, logger


@auto_load.task('aaas__client')
class AaasTask(TreeMultiTask):
    CTX_TASK_LIST_NAME = 'aaas__client:tasks'

    def conn(self, entrypoint:str=None, namespace=None, module=None, enable_https=False):
        client = AaasClient(
            entrypoint = entrypoint,
            namespace = namespace,
            enable_https = enable_https
        )

        if module:
            client.set_module(module)

        return {
            'client': client
        }
    
    def run(self, client:AaasClient, task_name, task_module=None, task_id=None, \
            task_configs=None, bind_arg=None, run_opts=None, state_hook=None):

        create_rst = client.create_task(
            task_name=task_name,
            task_id=task_id,
            module=task_module,
            configs=task_configs,
            bind_arg=bind_arg,
            run_opts=run_opts,
            state_hook=state_hook
        )

        task_id = create_rst.get('task_id')

        if task_id:
            tasks = self.context.list(self.CTX_TASK_LIST_NAME)
            tasks.append({
                'client': client.init_args(),
                'task_id': task_id,
            })

        logger.info('aaas__client create_task: %s', create_rst)
    
    def asdl(self, client:AaasClient, task_module=None, task_configs=None, bind_arg=None, run_opts=None):
        asdl_rst = client.asdl(
            module=task_module,
            configs=task_configs,
            bind_arg=bind_arg,
            run_opts=run_opts,
        )

        logger.info('aaas__client asdl_rst:\n%s', yaml_dumps(asdl_rst.get("result") or asdl_rst))

        return {
            "asdl": asdl_rst
        }
