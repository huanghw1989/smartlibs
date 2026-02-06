import time
from collections import Counter

try:
    from confluent_kafka import Producer, Consumer
    from confluent_kafka.admin import AdminClient, NewTopic
except:
    from smart.utils.lang.UnSupport import UnSupport
    Producer = Consumer = AdminClient = NewTopic = UnSupport(
        'confluent_kafka', 
        tip='Your should run cmd `pip install confluent_kafka` first'
    )

from smart.utils.serialize import TypeObjSerializer
from smart.utils.list import list_safe_iter

from smart.utils.__logger import logger_utils as logger


class KafkaQueue:
    # 配置文档参见: https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    # 缺省消费者组
    Default_Group_Id = 'default'
    # 缺省消费者的初始偏移量, earliest, beginning, latest
    Default_Auto_Offset_Reset = 'earliest'
    # 接收数据的最小轮询间隔
    Min_Pool_Interval = 1.0
    # 缺省Topic分区数, 影响并行度与吞吐量, 一般配置节点数量*(1-2)
    Default_Num_Partitions = 3
    # 缺省数据复制的数目, 影响高可用性, 一般kafaka集群配置2-3
    Default_Replication_Factor = 1

    def __init__(self, servers=None, host='localhost', port:int=9092, 
                admin_client_opts:dict=None, consumer_opts:dict=None, producer_opts:dict=None) -> None:
        """Kafka队列

        Args:
            servers (str|list, optional): 服务端列表. Defaults to None.
            host (str, optional): 服务端域名, servers参数非空时本参数无效. Defaults to 'localhost'.
            port (int, optional): 服务端端口, servers参数非空时本参数无效. Defaults to 9092.
            admin_client_opts (dict, optional): AdminClient类初始化的配置. Defaults to None.
            consumer_opts (dict, optional): Consumer类初始化的配置. Defaults to None.
            producer_opts (dict, optional): Producer类初始化的配置. Defaults to None.
        """
        if not servers:
            servers = host + ':' + str(port)
        self._bootstrap_servers = servers
        self.__admin_client_opts = admin_client_opts or {}
        self.__consumer_opts = consumer_opts or {}
        self.__producer_opts = producer_opts or {}
        self.__admin_client = None
        self.__producer = None
        self.__consumer = None
        self.__consumer_auto_commit = None
        self.__key_counter = Counter()
        self._log_delivery_report = False
        self._uncommit_msg_list = []
        self._subscribed_topics = set()

    def __get_servers_str(self):
        _servers = self._bootstrap_servers
        return ",".join(_servers) if isinstance(_servers, (list, tuple)) else _servers
    
    @property
    def admin_client_opts(self) -> dict:
        """AdminClient类初始化的配置

        Returns:
            dict: 配置
        """
        return self.__admin_client_opts
    
    @admin_client_opts.setter
    def admin_client_opts(self, opts):
        self.__admin_client_opts = opts if opts is not None else {}

    @property
    def consumer_opts(self) -> dict:
        """Consumer类初始化的配置

        Returns:
            dict: 配置
        """
        return self.__consumer_opts
    
    @consumer_opts.setter
    def consumer_opts(self, opts):
        self.__consumer_opts = opts if opts is not None else {}

    @property
    def producer_opts(self) -> dict:
        """Producer类初始化的配置

        Returns:
            dict: 配置
        """
        return self.__producer_opts
    
    @producer_opts.setter
    def producer_opts(self, opts):
        self.__producer_opts = opts if opts is not None else {}
    
    def update_consumer_opts(self, auto_commit:bool = None):
        """修改消费者配置

        Args:
            auto_commit (bool, optional): 自动确认接收, 缺省None等同于True. Defaults to None.
        """
        if auto_commit is not None:
            self.consumer_opts.update({
                'enable.auto.commit': auto_commit
            })

    def admin_client(self):
        """获取Kafka管理客户端(单例模式)

        Returns:
            AdminClient: Kafka管理客户端
        """
        if self.__admin_client is None:
            self.__admin_client = AdminClient({
                'bootstrap.servers': self.__get_servers_str(),
                **self.__admin_client_opts
            })
        return self.__admin_client
    
    def create_topic(self, topic_name_or_list, num_partitions:int=None, replication_factor:int=None, replica_assignment=None, topic_config=None, 
                operation_timeout=None, request_timeout=None, validate_only:bool=False, wait:bool=True):
        """创建topic

        topic_config参考: https://kafka.apache.org/documentation.html#topicconfigs

        Args:
            topic_name_or_list (str|list): topic名称或topic名称列表
            num_partitions (int, optional): 分区数, 缺省 KafkaQueue.Default_Num_Partitions.
            replication_factor (int, optional): 数据复制的数目, 缺省 KafkaQueue.Default_Replication_Factor.
            replica_assignment (list, optional): 副本指派. Defaults to None.
            topic_config (dict, optional): Topic配置. Defaults to None.
            operation_timeout (float, optional): 创建topic的操作超时时间. Defaults to None.
            request_timeout (_type_, optional): 整个请求的超时时间, 包含broker lookup, request transmission, operation time on broker, and response. Defaults to None.
            validate_only (bool, optional): 只验证请求参数合法, 不实际创建Topic. Defaults to False.
            wait (bool, optional): 是否等待创建完成, False是异步操作. Defaults to True.

        Returns:
            dict: {topic_name: Future}
        """
        if num_partitions is None: num_partitions = self.Default_Num_Partitions
        if replication_factor is None: replication_factor = self.Default_Replication_Factor
        new_topic_kwargs = {}
        if replica_assignment:
            new_topic_kwargs['replica_assignment'] = replica_assignment
        if topic_config:
            new_topic_kwargs['config'] = topic_config

        new_topics = list(NewTopic(
            topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
            **new_topic_kwargs
        ) for topic_name in list_safe_iter(topic_name_or_list))

        create_kwargs = {}
        if operation_timeout is not None:
            create_kwargs['operation_timeout'] = operation_timeout
        if request_timeout is not None:
            create_kwargs['request_timeout'] = request_timeout

        client = self.admin_client()
        topic_future_map = client.create_topics(
            new_topics,
            validate_only = validate_only,
            **create_kwargs
        )
        if wait:
            for topic, future in topic_future_map.items():
                future.result() # The result itself is None
        return topic_future_map
    
    def delete_topic(self, topic_name_or_list, operation_timeout=None, request_timeout=None, wait:bool=True):
        """删除Topic

        Args:
            topic_name_or_list (str|list): topic名称或topic名称列表
            operation_timeout (float, optional): 创建topic的操作超时时间. Defaults to None.
            request_timeout (_type_, optional): 整个请求的超时时间, 包含broker lookup, request transmission, operation time on broker, and response. Defaults to None.
            wait (bool, optional): 是否等待创建完成, False是异步操作. Defaults to True.

        Returns:
            dict: {topic_name: Future}
        """
        client = self.admin_client()
        topics = list(list_safe_iter(topic_name_or_list))
        _kwargs = {}
        if operation_timeout is not None:
            _kwargs['operation_timeout'] = operation_timeout
        if request_timeout is not None:
            _kwargs['request_timeout'] = request_timeout

        topic_future_map = client.delete_topics(
            topics,
            **_kwargs
        )
        if wait:
            for topic, future in topic_future_map.items():
                future.result() # The result itself is None
        return topic_future_map
    
    def list_topics(self, topic = None, timeout:float=-1):
        """Request metadata from the cluster. 
        This method provides the same information as listTopics(), describeTopics() and describeCluster() in the Java Admin client.

        Args:
            topic (str, optional): If specified, only request information about this topic, else return results for all topics in cluster. Warning: If auto.create.topics.enable is set to true on the broker and an unknown topic is specified, it will be created. Defaults to None.
            timeout (float, optional): The maximum response time before timing out, or -1 for infinite timeout. Defaults to -1.
        """
        client = self.admin_client()
        data = client.list_topics(topic, timeout=timeout)
        return data.topics


    def get_producer(self):
        """获取Producer生产者客户端(单例模式)

        Returns:
            Producer: 生产者客户端
        """
        producer = self.__producer
        if producer is None:
            _config = {}
            _config.update(self.producer_opts)
            _config['bootstrap.servers'] = self.__get_servers_str()
            self._producer_config = _config
            producer = self.__producer = Producer(_config)
        return producer
    
    def get_consumer(self):
        """获取Consumer消费者客户端(单例模式)

        Returns:
            Consumer: 消费者客户端
        """
        consumer = self.__consumer
        if consumer is None:
            _config = {
                'group.id': self.Default_Group_Id,
                'auto.offset.reset': self.Default_Auto_Offset_Reset
            }
            _config.update(self.consumer_opts)
            _config['bootstrap.servers'] = self.__get_servers_str()
            self.__consumer_auto_commit = _config.get('enable.auto.commit', True)
            self._consumer_config = _config
            consumer = self.__consumer = Consumer(_config)
        return consumer
    
    def _delivery_report(self, err, msg):
        """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
        if err is not None:
            raise Exception(err)
        elif self._log_delivery_report:
            logger.debug('Message delivered to %s [%s]', msg.topic(), msg.partition())
    
    def __msg_key(self, topic):
        key = self.__key_counter[topic]
        self.__key_counter[topic] = key+1
        return str(key)
    
    def send_one(self, item, topic=None, item_topic_key='_send_topic', partition:int=None, wait:bool=True, auto_msg_key=False):
        """发送单条数据

        Args:
            item (dict|bytes): 可通过json序列化的数据
            topic (str, optional): topic名称. Defaults to None.
            item_topic_key (str, optional): item的键, 用于动态指定topic. Defaults to '_send_topic'.
            partition (int, optional): 分区号. Defaults to None.
            wait (bool, optional): 是否等待结果返回. Defaults to True.
            auto_msg_key (bool, optional): 是否自动生成msg的key, 会用于做分区路由. Defaults to False.
        """
        _topic, producer_kwargs = topic, {}
        if isinstance(item, bytes):
            byte_data = item
        else:
            _topic = item.pop(item_topic_key, topic) if item_topic_key else topic
            byte_data = TypeObjSerializer.encode(item)
        assert _topic
        if partition is not None:
            producer_kwargs['partition'] = partition
        if auto_msg_key:
            producer_kwargs['key'] = self.__msg_key(topic)
        producer = self.get_producer()
        producer.poll(0)
        producer.produce(
            _topic, 
            byte_data,
            on_delivery=self._delivery_report,
            **producer_kwargs
        )
        if wait:
            producer.flush()

    def send_all(self, item_iter, topic=None, partition:int=None, send_end_cmd=True, 
            item_topic_key='_send_topic', item_msg_key=None, flush_step:int=1, auto_msg_key=False):
        """发送所有数据

        Args:
            item_iter (generator): item生成器
            topic (str, optional): topic名称. Defaults to None.
            partition (int, optional): 分区号. Defaults to None.
            send_end_cmd (bool, optional): 是否发送结束命令. Defaults to True.
            item_topic_key (str, optional): item的键, 用于动态指定topic. Defaults to '_send_topic'.
            item_msg_key (_type_, optional): item的键, 用于指定msg的key. Defaults to None.
            flush_step (int, optional): 多少条数据执行一次flush. Defaults to 1.
            auto_msg_key (bool, optional): 是否自动生成msg的key, 会用于做分区路由. Defaults to False.
        """
        producer = self.get_producer()
        b_flush = False
        for i, item in enumerate(item_iter):
            _topic, _msg_key, producer_kwargs = topic, None, {}
            if isinstance(item, bytes):
                byte_data = item
            else:
                _topic = item.pop(item_topic_key, topic) if item_topic_key else topic
                byte_data = TypeObjSerializer.encode(item)
                _msg_key = item.pop(item_msg_key, None) if item_msg_key else None
            assert _topic
            if partition is not None:
                producer_kwargs['partition'] = partition
            if _msg_key:
                producer_kwargs['key'] = _msg_key
            elif auto_msg_key:
                producer_kwargs['key'] = self.__msg_key(topic)
            producer.poll(0)
            producer.produce(
                _topic, 
                byte_data,
                on_delivery=self._delivery_report,
                **producer_kwargs
            )
            if flush_step <= 1 or (i+1) % flush_step == 0:
                producer.flush()
                b_flush = False
            else:
                b_flush = True
        if send_end_cmd and topic:
            byte_data = TypeObjSerializer.encode({'type':'end'}, 'cmd')
            producer.poll(0)
            producer.produce(
                topic, 
                byte_data,
                on_delivery=self._delivery_report,
                **producer_kwargs
            )
            b_flush = True
        if b_flush:
            producer.flush()

    def __consumer_poll(self, consumer, timeout, pool_interval):
        if timeout == 0:
            return consumer.poll(0)
        end_ts = (time.time() + timeout) if timeout else None
        while True:
            _timeout = min(end_ts-time.time(), pool_interval) if end_ts else pool_interval
            if _timeout <= 0:
                break
            msg = consumer.poll(_timeout)
            if msg is not None:
                if not self.__consumer_auto_commit:
                    self._uncommit_msg_list.append(msg)
                return msg
        return None
    
    def recv_one(self, topic_name_or_list, timeout:float=None, pool_interval:float=10, 
            with_msg_key:str=None, skip_err_item:bool=False):
        """接收一条数据

        Args:
            topic_name_or_list (str|list): topic名称或topic名称列表
            timeout (float, optional): 接收超时时间. Defaults to None.
            pool_interval (float, optional): 长轮询间隔. Defaults to 10.
            with_msg_key (str, optional): 将msg的key放入到指定item键. Defaults to None.
            skip_err_item (bool, optional): 跳过decode错误的item. Defaults to False.

        Raises:
            Exception: 接收数据出错

        Returns:
            tuple: (type, item); type是None表示数据, cmd表示命令
        """
        consumer = self.get_consumer()
        self.subscribe(topic_name_or_list)
        pool_interval = max(self.Min_Pool_Interval, pool_interval)
        while True:
            msg = self.__consumer_poll(consumer, timeout, pool_interval)
            if msg is None:
                return None, None
            err = msg.error()
            if err:
                raise Exception("KafkaQueue.recv_one error: "+str(err))
            msg_content = msg.value()
            try:
                type, item = TypeObjSerializer.decode(msg_content)
                if with_msg_key and isinstance(item, dict):
                    item[with_msg_key] = msg.key()
                return type, item
            except Exception as e:
                if skip_err_item:
                    logger.warning("KafkaQueue.recv decode error, msg=%s, err=%s", msg_content, e)
                    continue
                else:
                    logger.error("KafkaQueue.recv decode error, msg=%s", msg_content)
                    raise e
    
    def recv_all(self, topic_name_or_list, timeout:float=None, pool_interval:float=10, 
                is_daemon:bool=False, with_msg_key:str=None, skip_err_item:bool=False):
        """接收所有数据(直至超时或接收到结束命令)

        Args:
            topic_name_or_list (str|list): topic名称或topic名称列表
            timeout (float, optional): 接收超时时间. Defaults to None.
            pool_interval (float, optional): 长轮询间隔. Defaults to 10.
            is_daemon (bool, optional): 是否守护进程, True则忽略end命令, 只响应exit命令. Defaults to False.
            with_msg_key (str, optional): 将msg的key放入到指定item键. Defaults to None.
            skip_err_item (bool, optional): 跳过decode错误的item. Defaults to False.

        Raises:
            Exception: 接收数据出错

        Yields:
            dict: item数据
        """
        consumer = self.get_consumer()
        self.subscribe(topic_name_or_list)
        pool_interval = max(self.Min_Pool_Interval, pool_interval)
        msg = None
        while True:
            msg = self.__consumer_poll(consumer, timeout, pool_interval)
            if msg is None:
                break
            err = msg.error()
            if err:
                raise Exception("KafkaQueue.recv_all error: "+str(err))
            msg_content = msg.value()
            try:
                type, item = TypeObjSerializer.decode(msg_content)
                if with_msg_key and isinstance(item, dict):
                    item[with_msg_key] = msg.key()
            except Exception as e:
                if skip_err_item:
                    logger.warning("KafkaQueue.recv decode error, msg=%s, err=%s", msg_content, e)
                    continue
                else:
                    logger.error("KafkaQueue.recv decode error, msg=%s", msg_content)
                    raise e
            if type == 'cmd':
                item = item or {}
                cmd_type = item.get('type')
                end_types = ('exit',) if is_daemon else ('end', 'exit')
                if cmd_type in end_types:
                    logger.debug('KafkaQueue.recv_all end by cmd: %s', item)
                    break
                else:
                    logger.debug('KafkaQueue.recv_all ignore cmd: %s', item)
                continue
            yield item
    
    def commit(self):
        if not len(self._uncommit_msg_list):
            return 0
        consumer = self.get_consumer()
        i = 0
        while len(self._uncommit_msg_list):
            msg = self._uncommit_msg_list.pop(0)
            consumer.commit(msg)
            i += 1
        return i
    
    def unsubscribe(self):
        consumer = self.get_consumer()
        consumer.unsubscribe()
        self._subscribed_topics.clear()
    
    def subscribe(self, topic_name_or_list):
        consumer = self.get_consumer()
        topics = list(list_safe_iter(topic_name_or_list))
        _topics = [topic for topic in topics if topic not in self._subscribed_topics]
        if _topics:
            consumer.subscribe(_topics)
        self._subscribed_topics.update(_topics)

    def send_end_cmd(self, topic, partition:int=None, wait=True, cmd_type:str=None):
        """发送结束命令

        Args:
            topic (str): topic名称. Defaults to None.
            partition (int, optional): 分区号. Defaults to 0.
            wait (bool, optional): 是否等待结果返回. Defaults to True.
            cmd_type (str, optional): 命令类型, 缺省None表示end; 可选exit用于结束is_daemon=True的recv_all函数
        """
        cmd_type = cmd_type or 'end'
        cmd_data = {'type': cmd_type}
        item = TypeObjSerializer.encode(cmd_data, 'cmd')
        self.send_one(item, topic=topic, partition=partition, wait=wait)