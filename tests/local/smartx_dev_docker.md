
# 本地开发环境搭建
* 本地开发启动redis服务
```
# 启动redis
## 本地网络连接redis
### 连接方式(本地网络): redis.Redis(host='localhost', port=6379)
> docker run -d --name my_redis -p 6379:6379 redis:6
### 关闭服务
> docker stop my_redis && docker rm my_redis

## 容器网络连接redis
### 单节点redis: redis.Redis(host='redis-local', port=6380)
> docker-compose -f tests/local/docker/redis-standalone.yml up -d
### 关闭服务
> docker-compose -f tests/local/docker/redis-standalone.yml down

### redis集群: redis.cluster.RedisCluster(host='redis-node-0', port=6379, password='bitnami')
> docker-compose -f tests/local/docker/redis-cluster.yml up -d
### 关闭服务
> docker-compose -f tests/local/docker/redis-cluster.yml down
批量清除volume: 
for i in {0..5}; do docker volume rm docker_redis-cluster_data-$i; done
单个清除volume:
docker volume rm docker_redis-cluster_data-0
docker volume rm docker_redis-cluster_data-1
docker volume rm docker_redis-cluster_data-2
docker volume rm docker_redis-cluster_data-3
docker volume rm docker_redis-cluster_data-4
docker volume rm docker_redis-cluster_data-5
```
