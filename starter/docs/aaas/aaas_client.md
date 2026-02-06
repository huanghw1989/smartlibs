# aaas client
* 参考: [Tests](../../../tests/aaas/test_client.py)

* 代码示例

```
from smart.aaas.client import AaasClient

client = AaasClient(
    entrypoint = 'http://127.0.0.1:80',
    namespace = 'test'
)
client.set_module('starter.aaas.client')

asdl = client.asdl()
print('ASDL:', asdl)

create_task_rst = client.create_task(
    task_name = 'task:tools__tool.range~@tools__print.item_iter',
    bind_arg = {
        'tools__tool.range': {
            'start': 5,
            'end': 15,
            'step': 2,
        }
    }
)
print('create_task:', create_task_rst)
```
