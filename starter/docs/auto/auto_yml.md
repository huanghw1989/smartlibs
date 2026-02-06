# Auto Yml
smart_auto 框架使用 auto yml 文件驱动任务自动化.  

* 参考示例: [auto_yml example](../../helloworld/auto.yml)

* 配置格式使用`yaml 1.1`协议: [yaml](https://yaml.org/spec/1.1/); 参考: [pyyaml](https://pyyaml.org/wiki/PyYAMLDocumentation)



## root_node
* version: 当前版本为1.0; 写其它值目前不会产生不利影响, 但未来可能会产生兼容性问题
* configs: [配置节点]()
* tasks: [任务节点](#tasknode)
* trees: [任务树节点](#treenode)
* import: [导入文件](#import_node)
* hooks: [勾子函数节点](#hook_node)



## config_node
* 配置节点可以是任意深度的字典结构, 可通过多种 [autowired机制](./autowired.md#bind_config) 注入到任务类函数; 

* 基础示例
  
```
configs:
  example_task:
    default:
      start: 5
```

**支持的语法**
* template: [模版](#syntax_template)
* if: [条件](#syntax_if)
* extend: [继承](#syntax_extend)



## task_node
* 基础结构

```
tasks:
  __load__:
    task_module_path_pattern:
      as_module: rename_module | prefix_module.
      alias_module: rename_module | prefix_module.

  module_name.task_name:
    class: dotted_import_path
    alias:
      - alias_task_name
    def:
      method_a:
        bind_config:
          - dotted_config_path1
          - dotted_config_path2
        bind_arg:
          kwarg1: arg_val1
          kwarg2: arg_val2
        bind_obj:
          arg_name:
            path: dotted_cls_path
            config:
              - dotted_config_path3
              - dotted_config_path4
```

**task_opts**:  
* alias: 任务别名

**task_method_opts**:  
* bind_config, bind_arg, bind_obj: 参见[autowired机制](./autowired.md)
  
**__load__**:
* task_module_path_pattern: 以'.'分割的模块路径名, 支持'*'匹配文件名, 应对应到.py文件; 将自动加载使用 [auto_load装饰器](./autowired.md#autoload%e8%a3%85%e9%a5%b0%e5%99%a8) 的任务类
  
* task_module_path_pattern支持点相对路径, 参考 [Glossary](#glossary) 

**load_opts**:
* as_module: 重命名 auto_load装饰器 定义的任务名; 值以'.'结尾时, 表示在原任务名之前追加字符串; 否则, 只取原任务名的最后一个'.'之后的字符
  
* alias_module: 重命名 auto_load装饰器 定义的任务别名; 重命名方法同 as_module

**example**:
* 示例  

```
tasks:
  __load__:
    starter.helloworld.*:
      as_module: 
      as_module: starter
    auto_tasks.*.*:
      as_module: lib.
    auto_tasks.tools.*:
      as_module: lib
      alias_module: lib.

  starter.example_task:
    class: starter.helloworld.first_task.ExampleTask
    def:
      range:
        bind_config:
          - example_task.default
```

**other**:
* 简易写法
  
```
tasks:
  __load__:
    - task_module_path_pattern

  module_name.:
    task_name:
      class: dotted_import_path
      alias: alias_task_name

    task_name2:
      class: dotted_import_path
```

*等同于*:  

```
tasks:
  __load__:
    task_module_path_pattern:

  module_name.task_name:
    class: dotted_import_path
    alias: 
      - alias_task_name

  module_name.task_name2:
    class: dotted_import_path
```


## tree_node

**概念**
* 作用: 定义任务树列表
  
* tree: 任务树, 每个任务最多一个前置任务, 可以有多个后置任务, 不能出现环形依赖; 依赖的任务间通过数据管道(pip)发送数据

**数据管道**
* pip: 数据管道, 为任务树的依赖任务之间提供数据队列 
  
* 发送机制为广播, 即前置任务同时向多个后置任务发送相同数据, 后置任务不能向前置任务发送数据
  
* 前置任务调用 send_data 函数发送数据到管道, 后置任务调用 recv_data 函数接收数据
  
* 前置任务运行结束后, 缺省会自动发送结束命令到数据管道; recv_data 函数接收到结束命令后, 将结束数据生成器, 并不会将结束命令返回给调用者


**结构**
* 基础结构

```
trees:
  tree_name:
    __sibling__:
      common_run_opt_key: opt_val
    __flow__:
      - task_expression1
      - task_expression2
    task_expression:
      bind_config:
        - dotted_config_path
      join:
        - 
          join_method_l1_a:
            bind_config:
              - dotted_config_path
          join_method_l1_b:
        - join_method_l2_a:
      prev: task_key
      next:
        - task_key
      worker_num: int_val(default: None)
      send_end_cmd: bool_val(default: True)
      max_queue_size: int_val(default: None)
      remote_debug: bool_val(default: False)
```

* sibling节点: 将节点下的选项拷贝每个兄弟节点
  
* flow节点: 通过任务表达式定义任务, 并自动设置前后依赖关系

* prev, next: 设置任务的前后依赖关系
  
* worker_num: 任务单元的工作进程数; default None, 表示不启动独立工作进程, 即任务先后串联执行
  
* send_end_cmd: 前置任务结束时是否向后置任务发送结束命令
  
* max_queue_size: 数据管道最大hold数据量; default 0, 表示不限制
  
* remote_debug: 在任务工作进程启动时是否启用 ptvsd 远程调试; default False  
  worker_num大于1时, 只激活第一个工作进程到远程调试;  
  为避免数据管道数据被未激活调试到进程全部拉取, **建议**调试时设置worker_num=1  

  
**任务运行机制**
* worker_num缺省为None, 不启用独立工作进程, 即任务树的任务先后按依赖顺序执行; 
  
* 如果设置了worker_num, 将启用独立进程执行任务单元; 如果工作进程树大于1, 将抢占式地从数据管道接收数据
  
* 主任务函数与join函数在同一进程先后执行, 即归属同一个任务单元


## import_node
* 基础结构

```
import:
  - yml_dotted_path|yml_file_path
```

* yml_dotted_path(**推荐使用**): 点路径, 支持相对路径, 应对应yml文件; 参考 [Glossary](#glossary)  
starter.helloworld.auto 对应文件为 starter/helloworld/auto.yml  

* yml_file_path: 支持文件绝对路径和相对路径

* 文件相对路径: 相对 import 节点所在文件, 同级目录为'./', 上级目录为'../', 上上级目录为'../../'
  
* 注意: import使用**文件路径**方式时, 被 import 文件的 `task.__load__` 节点**不能使用**点相对路径


## hook_node
* 基础结构

```
hooks:
  - dotted_hook_cls_path1
  - dotted_hook_cls_path2
```

* dotted_hook_cls_path格式: package_name.(*sub_package_names).module_name.class_name

* hook class example

```
from smart.auto import AutoYmlHook
from smart.utils import AppEnv 

class EnvHook(AutoYmlHook):
    def before_parse(self, **kwargs):
        AppEnv.set('WORK_ROOT', '/home/app')

    def after_parse(self, **kwargs):
        pass
```


## syntax_template
* 作用: 执行模版表达式

* 语法结构

```
some_key:
  __template__:
    key_a: template_a
    key_b: template_b
```

*After Parse*:

```
some_key:
  key_a: template_str_eval(template_a)
  key_b: template_str_eval(template_b)
```


**模版**
* 环境变量模版: $ENV_NAME, ${ENV_NAME}, ${ENV_NAME:=default_val}

* 配置变量模版: ${config:dotted_config_key_path}, ${config:dotted_config_key_path:=default_val}


**示例**
* 模版语法示例

*example.yml*:
```
configs:
  ex_template:
    __template__:
      model_dir: $WORK_PATH/${MODEL_DIR}
      vocab_file: ${config:.model_dir}/${VOCAB_FILE_NAME:=vocab.txt}
```

*Set Env*:
> export WORK_PATH=/home/app
> export MODEL_DIR=dataset/bert/chinese_L-12_H-768_A-12

*Parsed Result*:
```
configs:
  ex_template:
    model_dir: /home/app/dataset/bert/chinese_L-12_H-768_A-12
    vocab_file: /home/app/dataset/bert/chinese_L-12_H-768_A-12/vocab.txt
```


* dotted_config_key_path 相对路径示例

```
configs:
  root_key:
    sub_key1:
      sub_key11: sub11
      __template__:
        sub_key12: ${config:.sub_key11}
        sub_key13: ${config:..sub_key2}
        sub_key14: ${config:...root_key2}
    sub_key2: sub2
  root_key2: root2
```

*解析结果*:
```
configs:
  root_key:
    sub_key1:
      sub_key11: sub11
      sub_key12: sub11
      sub_key13: sub2
      sub_key14: root2
    sub_key2: sub2
  root_key2: root2
```


## syntax_if
* 作用: 条件判断 (by 环境变量)

* 语法结构
```
some_key:
  __if__:
    ENV_NAME:
      val_case1:
        key_a: val_a1
        key_b: val_b1
      val_case2:
        key_a: val_a2
      __default__:
        key_a: val_default
```

*After Parse - default*:
```
some_key:
  key_a: val_default
```

*val_case1*:
> export ENV_NAME=val_case1

```
some_key:
  key_a: val_a1
  key_b: val_b1
```


## syntax_extend
* 从配置继承值

* 语法结构

```
some_key:
  __extend__:
    - dotted_config_key_path1
    - dotted_config_key_path2
```
  
* 示例

```
root_a:
  sub_key1: val_a1
  sub_key2: val_a2
root_b: 
  sub_key3: val_b3
root_c:
  __extend__:
    - root_a
    - root_b
    - no_exist_key
```

*After Parse*:
```
root_a:
  sub_key1: val_a1
  sub_key2: val_a2
root_b: 
  sub_key3: val_b3
root_c:
  sub_key1: val_a1
  sub_key2: val_a2
  sub_key3: val_b3
```

* __extend__节点的值可为字符串或数组, 值类型为 dotted_config_key_path  

参考: [template](#syntax_template) 的 **相对路径示例**  



## glossary
* 点路径(dotted_path): .替代文件分隔符, 同时隐去文件后缀;  
  
*示例*:  
```
import节点文件缺省后缀为'.yml'
文件路径: starter/helloworld/auto.yml
点路径: starter.helloworld.auto

tasks节点的__load__节点缺省后缀为'.py'
文件路径: starter/helloworld/first_task.py
点路径: starter.helloworld.first_task
```
  
* 点相对路径: 同级目录为'.', 上级目录为'..', 上上级目录为'...', 依次类推



## Learn more
* Next section: [autowired](./autowired.md)