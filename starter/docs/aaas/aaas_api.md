# aaas api

* 查看服务描述 (asdl: auto service description language)  
[推荐使用 Postman 测试后面的Api]  
> curl 'http://127.0.0.1/auto/run?module=starter.aaas.client&only_parse=1'


* 创建任务  
发送请求: 
> curl 'http://127.0.0.1/auto/run?module=starter.helloworld.auto&name=hook_task&bind_arg.example_task.range.start=5&task_ns=test'

响应结果:
```
{
    "code": 0,
    "data": {
        "task_id": "bcfd6834886711eb869facde48001122",
        "task_ns": "test",
        "module": "starter.helloworld.auto",
        "name": "hook_task",
        "run_opts": {
            "bind_arg.example_task.range.start": "5",
            "extra": {},
            "bind_arg": {}
        },
        "create_time": 1616126469.8762
    }
}
```

在运行smart_aaas的终端将看到任务执行日志  

* 查看任务执行结果
发送请求: 
> curl --location --request GET 'http://127.0.0.1:81/auto/task_info?task_id=bcfd6834886711eb869facde48001122&task_ns=test'

响应结果:  
```
{
    "code": 0,
    "data": {
        "task_id": "bcfd6834886711eb869facde48001122",
        "task_ns": "test",
        "module": "starter.helloworld.auto",
        "name": "hook_task",
        "run_opts": {
            "bind_arg.example_task.range.start": "5",
            "extra": {},
            "bind_arg": {}
        },
        "create_time": 1616126469.8762,
        "process": {
            "pid": 13197,
            "ppid": 13183
        },
        "done_flag": 1,
        "done_time": 1616126470.183182,
        "task_resp": {
            "hi": {
                "1": {
                    "from": "ExampleTask.check_state",
                    "step": 1,
                    "time": 1616126470.134312
                },
                "2": {
                    "from": "ExampleTask.check_state",
                    "step": 2,
                    "time": 1616126470.138442
                }
            }
        }
    }
}
```

响应数据说明:
1. data.process.pid: 有进程ID, 表示任务已经执行; 无进程ID, 表示任务正在排队;  
2. data.done_flag: >0 表示任务已经结束; 具体定义见[AutoTaskDoneFlag类](../../../smart/aaas/base.py)  
3. data.task_resp: 任务响应数据, 通过 TreeTask.context.response() 设置返回结果, 具体使用示例见 [ExampleTask.check_state](../../helloworld/example_task.py)
4. data.end_flag: 如果有end_flag, 表示任务在排队时触发了[end_task函数](../../../smart/aaas/auto_manage.py)  
   
