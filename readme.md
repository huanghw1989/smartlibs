Smart Platforms Libs

# 项目结构
**主框架**
* smart.auto: 自动化框架
* smart.aaas: auto as a service 自动化任务发布为rest服务
* smart.utils: 工具类
* smart.rest: simple rest server
* smart.rulenet: 规则网络 (原型版本)


**任务类库**
* auto_tasks.tools: 基础任务工具
* auto_tasks.jsonl: jsonl文件读写
* auto_tasks.redis: redis管道服务, 用于向aaas发送数据和读取结果
* auto_tasks.aaas: aaas客户端, 启动远程任务 



# How-to-Use
## Install

```bash
# 安装方法1
## 仓库安装
pip install smartlibs

## 源码打包安装
python3 setup.py sdist
pip install dist/smartlibs-0.1.4.tar.gz

# 记录安装文件
sudo python3 setup.py install --record logs/files.txt

## 更新
pip install --force-reinstall --no-deps smartlibs
```

# Quick Start
## smart_auto quick start
*查看命令说明*: `smart_auto -- --help`  
  
*Run Cmd Example*:
> smart_auto auto_tasks.tasks 'task:tools__tool.range~@tools__print.item_iter'

*Bind Arg*:
> smart_auto auto_tasks.tasks task:tools__tool.range~@tools__print.item_iter --bind_arg.tools__tool.range.size=20 --bind_arg.tools__print.item_iter.head=None

*Multi Tasks*:
> smart_auto auto_tasks.test helloworld,helloworld
> smart_auto auto_tasks.test '["task:tools__tool.range~@tools__print.item_iter","helloworld"]'


## smart_aaas quick start

*启动aaas服务*: `smart_aaas`  

*查看命令说明*: `smart_aaas -- --help`  

[推荐使用 Postman 测试后面的Api]  

*查看服务描述*(asdl: auto service description language): 
```
curl 'http://127.0.0.1/auto/run?module=starter.aaas.client&only_parse=1'
```

*创建任务*:  
```
curl 'http://127.0.0.1/auto/run?module=starter.aaas.client&name=task:tools__tool.range~@tools__print.item_iter'
在运行smart_aaas的终端将看到任务执行日志
```



# 名词解释
* smartlibs: smartnlp底层框架, 设计用于数据科学
* smart_auto: 任务自动化工具命令行, 等同于`python -m smart.auto.run`
* smart_aaas: 自动化发布成服务的工具命令行, 等同于`python -m smart.aaas.run`
  
**smart_auto**
* asdl: auto service description language 自动化服务描述语言, 基于 [yaml](https://yaml.org/spec/1.1/)
* auto yml: 使用asdl编写的yml文件
* task: 最小任务单元, 即使是单进程运行模式, 任务的设计应符合进程隔离; 即任务间应通过管道传递数据
* tree: 任务树, 每个任务最多一个前置任务, 可以有多个后置任务, 不能出现环形依赖
* task expression: 任务表达式, 设计简要的字符串规则, 可被解析为任务名、任务方法、连接方法、绑定配置
* task key: 任务表达式中的任务名、任务方法作为任务关键字, 同一个tree下task key不能重复; 如需复用任务函数, 可用$+数字追加到任务方法之后
* module: 以'.'分割的路径名(dotted_module_path), 追加'.yml'后缀应指向 auto yml 文件; 完整格式: python包名.下属文件路径(路径分隔符替换成'.').auto_yml文件名
* pip: 数据管道, 为任务树的依赖任务之间提供数据队列; 发送机制为广播, 即前置任务同时向多个后置任务发送相同数据, 后置任务不能向前置任务发送数据



# 教程
* [smart_auto doc](./starter/docs/auto/quick_start.md#Directory)

* [smart_aaas doc](./starter/docs/aaas/quick_start.md#Directory)



# 参考代码
* tests: 单元测试

**starter: 入门教程**
* starter.helloworld: 学习创建auto.yml, 编写任务类
  
* starter.aaas: aaas客户端和服务端示例 (通过Redis建立数据管道)


# 开发
## Windows环境

**注意**: Windows需在命令行执行`git config --global core.autocrlf input`  


## Start Redis Server

```
docker run -d --name myredis -p 6379:6379 redis redis-server --appendonly yes
```