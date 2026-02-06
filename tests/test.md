# 版本兼容性测试
* python3.8
```
# 在smartx项目根目录执行
> docker run -it --name test-smartx-py38 -v ${PWD}:/home/app -w /home/app -p 81:80 -p 5679:5678 python:3.8 bash

>
pip install -r requirements.txt
pip install numpy

## smart_auto
> python3 -m smart.auto.run auto_tasks.test helloworld

## smart_aaas
> python3 -m smart.aaas.run

> curl --location --request GET 'http://127.0.0.1:81/auto/run?module=starter.helloworld.auto&name=hook_task'

> curl --location --request GET 'http://127.0.0.1:81/auto/task_info?task_id=xxx'

# clean docker
docker stop test-smartx-py38
docker rm test-smartx-py38
```

* 更多版本
```
> docker run -it --name test-smartx-py36 -v ${PWD}:/home/app -w /home/app -p 81:80 -p 5679:5678 python:3.6 bash

> docker run -it --name test-smartx-py37 -v ${PWD}:/home/app -w /home/app -p 81:80 -p 5679:5678 python:3.7 bash

> docker run -it --name test-smartx-py39 -v ${PWD}:/home/app -w /home/app -p 81:80 -p 5679:5678 python:3.9 bash
docker stop test-smartx-py39
docker rm test-smartx-py39

> docker run -it --name test-smartx-py310 -v ${PWD}:/home/app -w /home/app -p 81:80 -p 5679:5678 python:3.10 bash
docker stop test-smartx-py310
docker rm test-smartx-py310
```