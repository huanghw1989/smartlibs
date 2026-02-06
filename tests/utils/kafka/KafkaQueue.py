# 创建topic: python3 -m tests.utils.kafka.KafkaQueue create_topic --topic=test_topic1
# 删除topic: python3 -m tests.utils.kafka.KafkaQueue delete_topic --topic=test_topic1
# 删除topic: python3 -m tests.utils.kafka.KafkaQueue list_topics
# 发送数据: 
#   python3 -m tests.utils.kafka.KafkaQueue send --topic=test_topic1 --num_item=2
#   python3 -m tests.utils.kafka.KafkaQueue send_all --topic=test_topic2 --num_item=3
# 接收数据: 
#   python3 -m tests.utils.kafka.KafkaQueue recv --topic=test_topic1 --auto_offset_reset=earliest --daemon=1
#   python3 -m tests.utils.kafka.KafkaQueue recv --topic=test_topic1 --timeout=0 --auto_offset_reset=latest
#   python3 -m tests.utils.kafka.KafkaQueue recv_all --topic=test_topic2 --group_id=test1 --auto_commit=False
# 新消费者组: python3 -m tests.utils.kafka.KafkaQueue recv --topic=test_topic1 --auto_offset_reset=earliest --daemon=1 --group_id=test3
# 发送退出命令: python3 -m tests.utils.kafka.KafkaQueue send_cmd --topic=test_topic1
import time, functools, pprint

from smart.utils.kafka.KafkaQueue import KafkaQueue
from tests.utils import logger


Test_Kafka_Hosts = [
    'localhost:31090',
]

Default_Test_Topic = 'test_topic1'

def _consumer_cb(type, *args, **kwargs):
    logger.info('consumer_cb %s args=%s kwargs=%s', type, args, kwargs)


def test_create_topic(topic=Default_Test_Topic, num_partitions:int=1, replication_factor:int=1):
    kq = KafkaQueue(servers=Test_Kafka_Hosts)
    create_rst = kq.create_topic(
        topic,
        num_partitions = num_partitions,
        replication_factor = replication_factor
    )
    print('create_topics result:', create_rst)

def test_delete_topic(topic=Default_Test_Topic):
    kq = KafkaQueue(servers=Test_Kafka_Hosts)
    delete_rst = kq.delete_topic(topic)
    print('delete_topic result:', delete_rst)

def test_list_topics(topic=None, timeout:float=-1, prefix:str=None):
    kq = KafkaQueue(servers=Test_Kafka_Hosts)
    topics = kq.list_topics(topic=topic, timeout=timeout)
    if prefix:
        topics = {
            k:v
            for k, v in topics.items()
            if k.startswith(prefix)
        }
    pprint.pprint(topics)

def test_send(topic=Default_Test_Topic, num_item:int=1, wait:bool=True, auto_msg_key:bool=False):
    kq = KafkaQueue(servers=Test_Kafka_Hosts)
    kq._log_delivery_report = True
    for i in range(num_item):
        item = {
            "idx": i,
            "ts": time.time()
        }
        kq.send_one(item, topic=topic, wait=wait, auto_msg_key=auto_msg_key)
        logger.info("send-%d: %s", i, item)
    if not wait:
        kq.get_producer().flush()
    logger.info("test_send end")

def test_recv(topic=Default_Test_Topic, timeout:float=None, auto_offset_reset=None, group_id=None, 
            daemon=False, with_msg_key='msg_key', auto_commit:bool=True):
    kq = KafkaQueue(servers=Test_Kafka_Hosts)
    if auto_offset_reset:
        kq.consumer_opts['auto.offset.reset'] = auto_offset_reset
    if group_id:
        kq.consumer_opts['group.id'] = group_id
    kq.consumer_opts.update({
        'stats_cb': functools.partial(_consumer_cb, ('stats',)),
        'error_cb': functools.partial(_consumer_cb, ('error',)),
        'throttle_cb': functools.partial(_consumer_cb, ('throttle',)),
        'on_commit': functools.partial(_consumer_cb, ('commit',)),
        # 'max.poll.interval.ms': 300.0 * 1000,
    })
    kq.update_consumer_opts(auto_commit=auto_commit)
    if daemon:
        timeout = None
    i = 0
    try:
        while True:
            type, item = kq.recv_one(
                topic, timeout=timeout, pool_interval=10, 
                with_msg_key=with_msg_key, skip_err_item=True
            )
            logger.info("recv-%d: %s, %s", i, type, item)
            i += 1
            if not auto_commit:
                # auto_commit=False时, 需执行commit确认成功处理完msg
                logger.debug("commit: %s", kq.commit())
            if daemon:
                continue
            if type is None and item is None:
                break
            if type == 'cmd':
                break
    finally:
        kq.unsubscribe()
        logger.debug('kq.unsubscribe')
    logger.debug("done commit: %s", kq.commit())
    _consumer_config = getattr(kq, '_consumer_config', None)
    logger.info("consumer_config: %s, uncommit_msg_list: %s", _consumer_config, kq._uncommit_msg_list)


def test_recv_all(topic=Default_Test_Topic, timeout:float=None, auto_offset_reset=None, group_id=None, 
            daemon=False, auto_commit:bool=True):
    kq = KafkaQueue(servers=Test_Kafka_Hosts)
    if auto_offset_reset:
        kq.consumer_opts['auto.offset.reset'] = auto_offset_reset
    if group_id:
        kq.consumer_opts['group.id'] = group_id
    kq.consumer_opts.update({
        'stats_cb': functools.partial(_consumer_cb, ('stats',)),
        'error_cb': functools.partial(_consumer_cb, ('error',)),
        'throttle_cb': functools.partial(_consumer_cb, ('throttle',)),
        'on_commit': functools.partial(_consumer_cb, ('commit',)),
    })
    kq.update_consumer_opts(auto_commit=auto_commit)
    if daemon:
        timeout = None
    item_iter = kq.recv_all(
        topic, timeout=timeout, pool_interval=10, 
        is_daemon=daemon, skip_err_item=True
    )
    try:
        for i, item in enumerate(item_iter):
            logger.info("recv-%d: %s", i, item)
            if not auto_commit:
                # auto_commit=False时, 需执行commit确认成功处理完msg
                logger.debug("commit: %s", kq.commit())
    finally:
        kq.unsubscribe()
        logger.debug('kq.unsubscribe')
    logger.debug("done commit: %s", kq.commit())
    _consumer_config = getattr(kq, '_consumer_config', None)
    logger.info("consumer_config: %s, uncommit_msg_list: %s", _consumer_config, kq._uncommit_msg_list)


def test_send_all(topic=Default_Test_Topic, num_item:int=2, partition:int=None, 
            send_end_cmd:bool=True, flush_step:int=1, auto_msg_key:bool=False):
    def _item_iter_fn():
        for i in range(num_item):
            item = {
                "idx": i,
                "ts": time.time()
            }
            logger.info("send-%d: %s", i, item)
            yield item
    _item_iter = _item_iter_fn()
    kq = KafkaQueue(servers=Test_Kafka_Hosts)
    kq._log_delivery_report = True
    kq.send_all(
        _item_iter, 
        topic=topic, 
        partition=partition, 
        send_end_cmd=send_end_cmd,
        flush_step=flush_step,
        auto_msg_key=auto_msg_key
    )
    logger.info("test_send_all end")


def test_send_cmd(topic=Default_Test_Topic, cmd='exit'):
    kq = KafkaQueue(servers=Test_Kafka_Hosts)
    kq._log_delivery_report = True
    kq.send_end_cmd(topic, cmd_type=cmd, wait=True)
    logger.info("test_send_cmd end")


def test_raw_recv(topic=Default_Test_Topic, group_id=None):
    kq = KafkaQueue(servers=Test_Kafka_Hosts)
    kq.consumer_opts['group.id'] = group_id
    kq.update_consumer_opts(auto_commit=True)

    consumer = kq.get_consumer()
    consumer.subscribe([topic])

    while True:
        msg = consumer.poll(1.0); print(msg and msg.value())
        if not msg: break

    msg = consumer.poll(10.0); print(msg and msg.value())


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)