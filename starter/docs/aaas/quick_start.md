# Quick_Start

## start aaas server
**启动aaas服务**
> smart_aaas


**启动命令选项**
* port: 监听的http端口
  
* worker_num: 自动化任务的并发工作数量; 一次自动化任务可能启动若干个工作进程, 因此实际开启的最大进程数量可能超过worker_num

* env.auto_m_clean_timing: 清理完成任务的定时任务间隔, 单位: second, 最小值: 5
  
* env.auto_m_task_info_ttl: 完成任务的存活时间, 单位: second, 最小值: 5
  
* 命令示例:  
> smart_aaas --port 81 --worker_num 4
> smart_aaas --env.auto_m_clean_timing=10 --env.auto_m_task_info_ttl=60


# Directory
* [Quick Start](./quick_start.md#Quick_Start)
  
* 自动化服务API: [aaas api](./aaas_api.md)
  
* 自动化服务客户端: [aaas client](./aaas_client.md)
