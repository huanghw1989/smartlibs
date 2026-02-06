# Quick_Start

## smart_auto command
**Run Cmd Example**
> smart_auto auto_tasks.tasks task:tools__tool.range~@tools__print.item_iter


**Bind Arg**
> smart_auto auto_tasks.tasks task:tools__tool.range~@tools__print.item_iter --bind_arg.tools__tool.range.size=20 --bind_arg.tools__print.item_iter.head=None


## smart_auto command args

**命令描述**  
```
smart_auto <dotted_module_path> <tree_name|task_expression> [options] --env.<env_name>=<env_value> --bind_arg.<task_name.method_name.arg_name>=<arg_val>
```

**参数说明**
* dotted_module_path: 以'.'分割的路径名(dotted_module_path), 追加'.yml'后缀应指向 auto yml 文件; 完整格式: python包名.下属文件路径(路径分隔符替换成'.').auto_yml文件名

* tree_name|task_expression: 任务树名称或任务表达式; 如果是任务表达式时, 应加'task:'区分
  
**options**
* only_parse: 只解析并打印auto_yml文件, 不执行任务
  
* extra: 额外的asdl字典, 设计非用于命令行参数, 如若调试时需要使用, 可传json字符串
  
* env.<env_name>: 设置应用环境变量, 可多选, 用于 asdl 的 template 语法和 if 语法; 程序中可通过`smart.utils.AppEnv`获取应用环境变量
  
* bind_arg.<task_name.method_name.arg_name>: 绑定变量到任务函数, 可多选



# Directory

* [Quick Start](./quick_start.md#Quick_Start)
  
* 任务表达式: [Task Expression](./task_exp.md)
  
* 自动化任务配置编写: [Auto Yml](./auto_yml.md)
  
* 自动装配机制: [Autowired](./autowired.md)