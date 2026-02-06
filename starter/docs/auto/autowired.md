# autowired
**自动装配**配置到任务类的指定函数的机制有三种: bind_config, bind_arg, bind_obj

- [autowired](#autowired)
  - [bind_config](#bind_config)
    - [auto_load装饰器](#auto_load装饰器)
  - [bind_arg](#bind_arg)
  - [bind_obj](#bind_obj)



## bind_config
* 说明: 将指定配置的值注入到任务类的函数参数

**bind_config的方式**
* bind_config 第一种方式是 [任务表达式](./task_exp.md#Base_Struct)中介绍的 dotted_config_pathes
  
* bind_config 另一种方式是 [任务节点](./auto_yml.md#task_node)
  
* bind_config 第三种形式是通过 [auto_load装饰器](#autoload%e8%a3%85%e9%a5%b0%e5%99%a8) 在目标函数指定; 该方式指定的是**缺省值**, 会被前两种方式覆盖


### auto_load装饰器
* Example Code

*starter/helloworld/example_task.py*:  
```
from smart.auto import AutoLoad, TreeMultiTask

auto_load = AutoLoad()

@auto_load.task('helloworld.example_task', alias=['example'])
class ExampleTask(TreeMultiTask):
    @auto_load.method(config=['example_task.range'])
    def range(self, start, end, step):
        for i in range(start, end, step):
            self.send_data(i)

@auto_load.func_task('helloworld.example_recv', config='example_task.recv')
def example_recv_task(task, start, end, step):
    for item in task.recv_data():
        print(item)
```

* Use In auto_yml file

*starter/helloworld/example.yml*:  
```
tasks:
  __load__:
    .*:
      as_module: starter
      alias_module: helloworld.
  
trees:
  example:
    __flow__:
      - starter.example_task.range
      - starter.example_recv
  example2:
    example_task.range:
  example3:
    helloworld.example.range:
```

*asdl*:  
```
tasks:
  starter.example_task:
    class: starter.helloworld.example.ExampleTask
    alias: helloworld.example
    def:
      range:
        bind_config:
          - example_task.range
  starter.example_recv:
    class: starter.helloworld.example.example_recv_task
    def:
      start:
        bind_config:
          - example_task.recv
  
trees:
  example:
    starter.example_task.range:
      next: 
        - starter.example_recv
    starter.example_recv:
      prev: starter.example_task.range
  example2:
    example_task.range:
  example3:
    helloworld.example:
```


## bind_arg
* 说明: 将指定值注入到任务类的函数参数

* 设计的使用场景1: 用于命令行参数调试任务时使用
  
```
smart_auto module_name tree_name|task_exp \
    --bind_arg.task_name.method_name.arg_name=arg_val \
    --bind_arg.task_name2.method_name2.arg_name=arg_val
```

* smart_auto 命令行示例
  
```
smart_auto auto_tasks.tasks task:tools__tool.range~@tools__print.item_iter --bind_arg.tools__tool.range.size=20 --bind_arg.tools__print.item_iter.head=20
```

*等同asdl*:
```
tasks:
  tools__tool:
    class: auto_tasks.tools.tool.ToolTask <- auto_tasks工具包的auto_load装饰器定义
    def:
      range:
        bind_arg:
          size: 20
  tools__print:
    class: auto_tasks.tools.t_print.PrintTask <- auto_tasks工具包的auto_load装饰器定义
    def:
      item_iter:
        bind_arg:
          head: 20
```


* 设计的使用场景2: 基于 smart_auto 的框架 smart_aaas 使用



## bind_obj
* bind_obj是高阶用法, 非必要时**不建议使用**

* 说明: 将对象注入到任务类的函数参数, 同时可将指定配置的值注入到对象的初始化参数

* 也可以注入函数, 指定配置的值注入到函数参数, 将函数返回值注入到指定任务类的函数参数

**使用方式**
* [任务节点](./auto_yml.md#task_node) 的 bind_obj

* auto_load 装饰器  

*Example Code*:  
```
import random
from smart.auto import AutoLoad, TreeMultiTask

auto_load = AutoLoad()

def linear_dataset(size=1000, weight=12.3, bias=-11.1, noise=.1):
    def data_gen():
        for i in range(size):
            x = round(random.random() * 100, 5)
            y = weight * x + bias
            y *= 1 + random.random() * noise
            y = round(y, 5)
            yield {'x': x, 'y': y}
    return data_gen

@auto_load.func_task('linear_solve')
@auto_load.bind_obj(linear_dataset, config='linear_solve.linear_dataset')
@auto_load.bind_obj(linear_dataset, config='linear_solve.linear_dataset2', arg_name='linear_dataset2')
@auto_load.bind_obj('tensorflow', arg_name='tf')
def linear_solve(task, linear_dataset, linear_dataset2, tf):
    pass
```


* 示例教程: [bind_obj.py](../../helloworld/bind_obj.py)

