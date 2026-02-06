import asyncio
import threading

import websockets
from websockets.client import WebSocketClientProtocol



class WebSocketContext:
    def __init__(self):
        super().__init__()
        self.__websocket:WebSocketClientProtocol = None
        self.__wait_event = threading.Event()
        self.__await_event = asyncio.Event()
        self.stop_flag = False

    def get_loop(self):
        try:
            return asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def set_websocket(self, websocket:WebSocketClientProtocol):
        self.__websocket = websocket

        event = self.__wait_event
        event2 = self.__await_event
        loop = self.get_loop()

        if event is not None:
            if websocket is None:
                event.clear()
                event2.clear()
            else:
                event.set()
                event2.set()

    def get_websocket(self):
        return self.__websocket
    
    def wait_websocket(self, timeout:int=None):
        ws = self.__websocket

        if ws is not None:
            return ws

        if timeout is not None and timeout < 0:
            timeout = None
        
        self.__wait_event.wait(timeout)

        return self.__websocket
    
    async def await_websocket(self, timeout:int=None):
        ws = self.__websocket

        if ws is not None:
            return ws

        if timeout is not None and timeout < 0:
            timeout = None
        
        try:
            await asyncio.wait_for(
                self.__await_event.wait(), timeout=timeout
            )
        except asyncio.TimeoutError:
            pass
        
        return self.__websocket
        
