
# 使用uwsgi
```
### 运行服务端
> uwsgi --http :8081 --processes 2 --threads 4 --module "smart.aaas.wsgi:app()" --pyargv "--worker_num 10 --task_log logs/task"

### 压力测试
1. 启动任务
> python3 -m smart.auto.run tests.aaas.example1.client test_guid_svr --env.port=8081
服务端日志: 
2022-11-22 15:07:07,138 INFO  [64119] aaas  task callback-done (None, '463f62ba6a3411edace5acde48001122') {'result': {}}

2. 并发测试
> ab -n 500 -c 100 "http://127.0.0.1:8081/auto/task_info?task_id=463f62ba6a3411edace5acde48001122"
Concurrency Level:      100
Time taken for tests:   0.513 seconds
Complete requests:      500
Failed requests:        0

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    1   0.9      0       3
Processing:     8   92  22.6     93     125
Waiting:        4   92  22.6     92     124
Total:          8   92  21.9     93     125
```


# 使用http_server
```
### 运行服务端
> smart_aaas --port 8081 --worker_num 10 --task_log logs/task

### 压力测试
1. 启动任务
> python3 -m smart.auto.run tests.aaas.example1.client test_guid_svr --env.port=8081
服务端日志: 
2022-11-22 15:16:23,806 INFO  [65323] aaas  task callback-done (None, '920e5b486a3511edada1acde48001122') {'result': {}}

2. 并发测试
> ab -n 500 -c 100 "http://127.0.0.1:8081/auto/task_info?task_id=920e5b486a3511edada1acde48001122"
This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
apr_socket_recv: Connection reset by peer (54)
Total of 64 requests completed

> ab -n 500 -c 10 "http://127.0.0.1:8081/auto/task_info?task_id=920e5b486a3511edada1acde48001122"
This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
Send request failed!
apr_socket_recv: Connection reset by peer (54)
Total of 2 requests completed

> ab -n 500 -c 2 "http://127.0.0.1:8081/auto/task_info?task_id=920e5b486a3511edada1acde48001122"
Concurrency Level:      2
Time taken for tests:   0.862 seconds
Complete requests:      500
Failed requests:        0
Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       1
Processing:     2    3   3.2      3      40
Waiting:        2    3   3.2      3      40
Total:          2    3   3.2      3      40
```


# 使用ThreadingHTTPServer
python 3.7以上版本支持http.server.ThreadingHTTPServer

```
### 运行服务端
> python3.10 -m smart.aaas.run --port 8081 --worker_num 10 --task_log logs/task
...
2022-11-22 15:34:41,224 DEBUG [66871] rest  RestHttpServer use ThreadingHTTPServer

### 压力测试
1. 启动任务
> python3 -m smart.auto.run tests.aaas.example1.client test_guid_svr --env.port=8081
服务端日志: 
2022-11-22 15:35:15,582 INFO  [66874] aaas  task callback-done (None, '342588826a3811edb74facde48001122') {'result': {}}

> curl -v "http://127.0.0.1:8081/auto/task_info?task_id=342588826a3811edb74facde48001122"

2. 并发测试
> ab -n 500 -c 100 "http://127.0.0.1:8081/auto/task_info?task_id=342588826a3811edb74facde48001122"


> ab -n 50 -c 10 "http://127.0.0.1:8081/auto/task_info?task_id=920e5b486a3511edada1acde48001122"
apr_socket_recv: Connection reset by peer (54)
Total of 1 requests completed

> ab -n 500 -c 2 "http://127.0.0.1:8081/auto/task_info?task_id=920e5b486a3511edada1acde48001122"
```