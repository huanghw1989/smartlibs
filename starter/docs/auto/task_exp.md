# Task Expression

## Base_Struct
* base struct
  
```
task_name.main_method(dotted_config_pathes)~join_method(dotted_config_pathes),parallel_join_method(dotted_config_pathes)~next_join_method
```

* dotted_config_pathes struct
  
```
dotted_config_path_1+dotted_config_path_2+...+dotted_config_path_n
```

* task expression example
  
```
example_task.range(range.start_5 + range.step_2)~attach(sum__group3),st~log
```

*ASDL*:
```
{
    'example_task.range': {
        'bind_config': [
            'range.start_5',
            'range.step_2'
        ],
        'join': [
            {
                'attach': {
                    'bind_config': [
                        'sum__group3'
                    ]
                },
                'st': {}
            },
            {
                'log': {}
            }
        ]
    }
}
```


## Join_External_Task
* External Task Symbol: @
  
* Struct
  
```
task_name.main_method(...)~@other_task_name.ext_task_method(...)~iternal_task_method(...)
```

* Expression Example
  
```
tools__tool.range(range.start_5+range.step_2)~@tools__print.item_iter
```

* Example Command
  
```
smart_auto auto_tasks.tasks 'task:tools__tool.range(range.start_5+range.step_2)~@tools__print.item_iter'
```

* 注意: ext_task_method函数实质应为static, 首参数是task_name对应的任务实例, 并非other_task_name



## Learn more
* Next section: [Auto YML](./auto_yml.md)