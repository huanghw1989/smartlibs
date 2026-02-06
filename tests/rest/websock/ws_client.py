from smart.rest.websock.ws_client import WebsocketClient
import threading
import asyncio
import time
from queue import Queue


def client_send_data(client:WebsocketClient, n=3):
    print('client_send_data start', time.time())
    for i in range(n):
        data = 'pack '+str(i)
        client.send_data(data)
        # client.send_queue.put_nowait(data)
        time.sleep(.5)

    print('client_send_data end {} items'.format(n), time.time())

def client_recv_data(client:WebsocketClient, n=3):
    print('client_recv_data start', time.time())
    recv_queue = client.recv_queue
    for i in range(n):
        try:
            data = recv_queue.get(True, 3)
            print('recv', i, data, time.time())
        except asyncio.TimeoutError:
            print('recv TimeoutError', i, time.time())
        except asyncio.QueueEmpty:
            print('recv QueueEmpty', i, time.time())
            time.sleep(1)
            continue
    
    print('client_recv_data end', time.time())
    time.sleep(3)
    client.ctx.stop_flag = True

def test_client(host='127.0.0.1', port=8765):
    """测试ws_client
    websocket连接客户端在独立线程, 数据处理在主线程
    """
    num_pack = 3
    client = WebsocketClient(host, port)
    t_ws = threading.Thread(target=client.run_forever)
    t_ws.start()

    client._debug_log = True
    client.wait_websocket()
    print('test_client connected')

    t_recv = threading.Thread(target=client_recv_data, args=(client, num_pack))
    t_recv.start()

    for i in range(num_pack):
        client.send_data('test pack '+str(i))

    t_ws.join()
    t_recv.join()

def test_client2(host='127.0.0.1', port=8765):
    """测试ws_client
    websocket连接客户端在主线程, 数据处理在独立线程
    """
    client = WebsocketClient(host, port)

    client._debug_log = True
    client.loop.set_debug(True)

    loop = client.get_loop()
    t_send = threading.Thread(target=client_send_data, args=(client, 3))
    t_recv = threading.Thread(target=client_recv_data, args=(client, 3))
    t_send.start()
    t_recv.start()

    client.run_forever()
    print('test client2 end')
    t_send.join()
    t_recv.join()

if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)