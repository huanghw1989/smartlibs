import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from asyncio.queues import QueueFull, QueueEmpty
import websockets
import queue
import threading
import multiprocessing as mp

from .ws_ctx import WebSocketContext

from smart.rest.__logger import logger_rest


class WebsocketClient:
    def __init__(self, host, port, recv_queue:queue.Queue=None):
        super().__init__()
        self.ctx = WebSocketContext()
        self.server_addr = (host, port)

        if recv_queue is None:
            recv_queue = mp.Queue()

        self.recv_queue = recv_queue
        
        # send_queue和loop必须在run_forever所在的线程初始化
        self.__send_queue = None
        self.__loop = None

        self._debug_log = False
    
    def get_loop(self):
        try:
            return asyncio.get_event_loop()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    @property
    def loop(self):
        loop = self.__loop
        if loop is None:
            self.__loop = loop = self.get_loop()
        
        return loop
    
    @property
    def send_queue(self):
        send_queue = self.__send_queue
        if send_queue is None:
            self.__send_queue = send_queue = asyncio.Queue()
        
        return send_queue
    
    def get_server_uri(self):
        host, port = self.server_addr

        return 'ws://{}:{}'.format(
            host, str(port)
        )
    
    def send_data(self, data):
        self.loop.call_soon_threadsafe(
            self.send_queue.put_nowait, data)
    
    async def _do_connect(self):
        uri = self.get_server_uri()
        count = 0

        while not self.ctx.stop_flag:
            async with websockets.connect(uri) as websocket:
                self.ctx.set_websocket(websocket)

                while not self.ctx.stop_flag:
                    try:
                        recv_data = await asyncio.wait_for(websocket.recv(), 3.0)
                    except asyncio.TimeoutError:
                        continue
                    except BaseException as e:
                        logger_rest.warning('websocket recv error %s', e)
                        await asyncio.sleep(1)
                        break

                    if recv_data:
                        count += 1
                        self.recv_queue.put(recv_data)
                        if self._debug_log:
                            logger_rest.debug('websocket.recv %s item', count)
        
        logger_rest.info('WebsocketClient connect end')

    async def _handle_send_data(self):
        count = 0
        while not self.ctx.stop_flag:
            try:
                data = await asyncio.wait_for(self.send_queue.get(), 3.0)
            except asyncio.TimeoutError:
                continue

            count += 1

            for i in range(3):
                # max retry 3 times
                ws = await self.ctx.await_websocket(3.0)
                if ws is not None:
                    try:
                        await ws.send(data)
                    except websockets.exceptions.ConnectionClosedOK:
                        logger_rest.info('websocket send error caused by connection closed')
                        # self.ctx.set_websocket(None)
                        await asyncio.sleep(.5)
                        continue
                    
                    if self._debug_log:
                        logger_rest.debug('websocket.send %s item', count)
                    break
                await asyncio.sleep(.1)
        
        logger_rest.info('WebsocketClient handler end')

    def run_forever(self):
        self.loop.run_until_complete(
            asyncio.gather(
                self._do_connect(),
                self._handle_send_data()
            )
        )
    
    def wait_websocket(self, timeout=None):
        return self.ctx.wait_websocket(timeout=timeout)