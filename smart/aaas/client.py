import re, requests, json, time
import uuid

from smart.utils.base import ApiException
from smart.utils.dict import dict_safe_set, dict_safe_get
from smart.utils.number import safe_parse_int
from .__logger import logger


class AaasClient:
    Default_Retry_Num = 2
    Default_Retry_Interval = 3.0

    def __init__(self, entrypoint:str, namespace=None, enable_https=False, **kwargs):
        if not re.match(r'^\w+\:\/\/', entrypoint):
            ep_proto = 'https' if enable_https else 'http'
            entrypoint = ep_proto + '://' + entrypoint
        
        self.entrypoint = entrypoint.rstrip('/')
        self.namespace = namespace
        self.module = None
        self._opt = {
            'retry_num': self.Default_Retry_Num,
            'retry_interval': self.Default_Retry_Interval
        }
        self._opt.update(kwargs)
    
    def init_args(self):
        return {
            'entrypoint': self.entrypoint,
            'namespace': self.namespace,
        }
    
    def set_module(self, module):
        self.module = module
        return self

    def task_uuid(self):
        """Generate Task UUID
        
        Returns:
            str -- uuid
        """
        return uuid.uuid1().hex

    def __parse_api_rst(self, resp):
        content = resp.content
        content = content.decode('utf8') if content is not None else None

        if content:
            full_data = json.loads(content)
            code = full_data.get('code')

            if code > 0:
                raise ApiException(full_data.get('msg'), code)

            return full_data.get('data')
        
        raise ApiException('null aaas response', 1)

    def __call_api(self, path:str, query={}, post_data=None, http_method=None, parse_fn:callable=None, retry_num:int=None, req_kwargs=None):
        if not path.startswith('/'):
            path = '/' + path

        if not http_method:
            http_method = 'get' if post_data is None else 'post'
        
        if not query.get('task_ns') and self.namespace:
            query['task_ns'] = self.namespace
        
        if parse_fn is None:
            parse_fn = self.__parse_api_rst

        api_url = self.entrypoint + path

        retry_num = retry_num or self._opt.get('retry_num') or 1
        retry_interval = max(self._opt.get('retry_interval'), 0.5)

        resp = None
        for i in range(retry_num):
            try:
                resp:requests.Response = requests.request(http_method, api_url, params=query, json=post_data, **(req_kwargs or {}))
                break
            except Exception as e:
                logger.warning("AaasClient call api failed %s/%s: %s", i+1, retry_num, e)
                if i < retry_num - 1:
                    time.sleep(retry_interval)
                else:
                    raise e

        return parse_fn(resp)
    
    def asdl(self, module=None, task_name=None, configs=None, bind_arg=None, run_opts=None):
        """Auto Service Descrption Language
        
        Keyword Arguments:
            module {str} -- module path, 缺省使用 set_module 函数设置的 module (default: {None})
        """
        module = module or self.module
        assert module is not None

        post_data = {}
        if configs:
            post_data['configs'] = configs

        if bind_arg:
            post_data['bind_arg'] = bind_arg

        if run_opts:
            post_data['run_opts'] = run_opts
        
        query = {
            'only_parse': 1,
            'name': task_name,
            'module': module
        }

        return self.__call_api('/auto/run', query, post_data)

    def create_task(self, task_name, task_id = None, module=None, 
            configs=None, bind_arg=None, run_opts=None, state_hook=None):
        module = module or self.module
        assert module is not None

        if not task_id:
            task_id = self.task_uuid()

        post_data = {}
        if configs:
            post_data['configs'] = configs

        if bind_arg:
            post_data['bind_arg'] = bind_arg

        if run_opts:
            post_data['run_opts'] = run_opts
        
        if state_hook:
            post_data['state_hook'] = state_hook
        
        query = {
            'name': task_name,
            'module': module,
            'task_id': task_id,
        }
        
        return self.__call_api('/auto/run', query, post_data=post_data)
    
    def task_info(self, task_id):

        return self.__call_api('/auto/task_info', {
            'task_id': task_id,
        })
    
    @staticmethod
    def _parse_log_stream(resp:requests.Response):
        headers = dict(resp.headers)
        stream = resp.iter_content(chunk_size=1, decode_unicode=False)
        def _line_iter_fn():
            prev = None
            for byte in stream:
                if byte == b'\n':
                    yield (prev or b'') + byte
                    prev = None
                else:
                    prev = byte if prev is None else prev + byte
            if prev:
                yield prev

        resp_dict = {
            'headers': headers,
            'info': {},
            'line_iter': _line_iter_fn()
        }
        for _name, _val in headers.items():
            _key_path = _name.lower().replace('-', '_').split('_', 1)
            if _key_path[0] in ('aaas', 'app'):
                dict_safe_set(resp_dict['info'], _key_path, _val)

        err_code = safe_parse_int(dict_safe_get(resp_dict, ('info', 'app', 'error_code'), 0))
        err_msg = dict_safe_get(resp_dict, ('info', 'app', 'error_msg'))
        if err_code:
            raise ApiException(err_msg, err_code)
        
        return resp_dict

    def task_log(self, task_id, pool_interval:int=10, pool_line:int=10, log_offset:int=0, 
                tail_mode:bool=False, tail_line:int=0, tail_follow:bool=False):
        return self.__call_api('/auto/task_log', {
            'task_id': task_id,
            'pool_interval': pool_interval,
            'pool_line': pool_line,
            'log_offset': log_offset,
            'tail_mode': tail_mode,
            'tail_line': tail_line,
            'tail_follow': tail_follow
        }, parse_fn=self._parse_log_stream, req_kwargs={'stream': True})
    
    def all_task(self):

        return self.__call_api('/auto/all_task')
    
    def end_task(self, task_id):

        return self.__call_api('/auto/end_task', {
            'task_id': task_id,
        })
    
    def shut_down(self):
        """关闭aaas服务, 需要运行smart_aaas时加--shuttable启用远程关闭命令
        """

        return self.__call_api('/admin/shut_down', http_method='get')


class AaasLogCat:
    def __init__(self, client:AaasClient, task_id, 
            pool_interval:int=10, pool_line:int=20) -> None:
        """Aaas服务任务日志查看器

        Args:
            client (AaasClient): Aaas服务客户端
            task_id (str): 任务ID
            pool_interval (int, optional): 取远程日志的轮询间隔. Defaults to 10.
            pool_line (int, optional): 取远程日志的轮询行数. Defaults to 20.
        """
        self._client = client
        self._task_id = task_id
        self._seek_pos = (0, 0)
        self._pool_interval = pool_interval
        self._pool_line = pool_line
        self._debug = False
        self._last_resp = None
        self._task_is_end = False
        self._not_ready = False
        self._retry_interval_not_ready = 1.0
    
    def seek(self, pos, begin_pos=None):
        """日志文件跳转到指定字节位置

        Args:
            pos (int): 字节位置
            begin_pos (int, optional): 位置区间的开始, 用于从后向前读取日志使用. Defaults to None.
        """
        self._seek_pos = (pos if begin_pos is None else begin_pos, pos)
    
    def tell(self, backward=False):
        """当前文件位置

        Args:
            backward (bool, optional): 是否从后向前读取. Defaults to False.

        Returns:
            int: 文件位置
        """
        return self._seek_pos[0 if backward else 1]
    
    def more(self, follow:bool=False, backward=False):
        """当前文件位置继续读取n行数据; 如果follow为True时, 继续读取新数据直至满足轮询间隔和轮询行数

        Args:
            follow (bool, optional): 是否继续读取新数据直至满足轮询结束条件, backward=False时follow固定为False. Defaults to False.
            backward (bool, optional): 是否向前反向读取数据. Defaults to False.

        Yields:
            byte: 一行日志, backward=False时顺序是从前往后, backward=True时顺序是从后往前
        """
        log_offset=self.tell(backward=backward)
        sig = -1 if backward else 1
        pool_line = self._pool_line * sig
        if backward:
            follow = False
        resp = self._client.task_log(self._task_id, 
            pool_interval=self._pool_interval,
            pool_line=pool_line,
            log_offset=log_offset,
            tail_mode=False,
            tail_follow=follow
        )
        self._last_resp = resp
        headers = resp.get('headers')
        info = resp.get('info')
        line_iter = resp.get('line_iter')
        if self._debug:
            logger.debug("AaasLogCat.more offset=%s, follow=%s, resp_headers=%s", log_offset, follow, headers)
        self._task_is_end = dict_safe_get(info, ('aaas', 'task_end')) in ('1', 'true', 'True')
        self._not_ready = dict_safe_get(info, ('aaas', 'not_ready')) in ('1', 'true', 'True')

        seek_offset_begin, seek_offset_end = log_offset, log_offset
        for line_data in line_iter:
            yield line_data
            if backward:
                seek_offset_begin -= len(line_data)
            else:
                seek_offset_end += len(line_data)
            self.seek(seek_offset_end, begin_pos=seek_offset_begin)
    
    def tail(self, line:int=0, follow:bool=False):
        """从文件末尾的倒数第line行数据向后读取; 如果follow为True时, 继续读取新数据直至满足轮询结束条件(间隔或行数)

        Args:
            line (int, optional): 从倒数第line行开始读取. Defaults to 0.
            follow (bool, optional): 是否继续读取新数据直至满足轮询结束条件. Defaults to False.

        Yields:
            byte: 一行日志, 顺序是从前往后
        """
        resp = self._client.task_log(self._task_id, 
            pool_interval=self._pool_interval,
            pool_line=self._pool_line,
            tail_mode=True,
            tail_line=line,
            tail_follow=follow
        )
        self._last_resp = resp
        headers = resp.get('headers')
        info = resp.get('info')
        line_iter = resp.get('line_iter')
        if self._debug:
            logger.debug("AaasLogCat.tail line=%s, follow=%s, resp_headers=%s", line, follow, headers)
        self._task_is_end = dict_safe_get(info, ('aaas', 'task_end')) in ('1', 'true', 'True')
        self._not_ready = dict_safe_get(info, ('aaas', 'not_ready')) in ('1', 'true', 'True')

        tail_n_offset = safe_parse_int(dict_safe_get(info, ('aaas', 'tail_n_offset')), None)
        seek_offset_begin, seek_offset_end = None, None
        if tail_n_offset is not None:
            self.seek(tail_n_offset)
            seek_offset_end = seek_offset_begin = tail_n_offset
        for line_data in line_iter:
            yield line_data
            if seek_offset_end is not None:
                seek_offset_end += len(line_data)
                self.seek(seek_offset_end, begin_pos=seek_offset_begin)
    
    def more_all(self, follow=False, backward=False):
        """从当前文件位置读取所有数据; 如果follow为True时, 继续读取新数据直至任务结束; 

        Args:
            follow (bool, optional): 是否继续读取新数据直至满足轮询结束条件, backward=False时follow固定为False. Defaults to False.
            backward (bool, optional): 是否向前反向读取数据. Defaults to False.

        Yields:
            byte: 一行日志, backward=False时顺序是从前往后, backward=True时顺序是从后往前
        """
        while True:
            line_iter = self.more(follow=follow, backward=backward)
            total_byte = 0
            for line in line_iter:
                yield line
                total_byte += len(line)
            if total_byte == 0 and self._task_is_end:
                break
            if self._not_ready:
                time.sleep(self._retry_interval_not_ready)
                continue

    def tail_all(self, line:int=0, follow:bool=False):
        """从倒数第line行数据读取所有数据; 如果follow为True时, 继续读取新数据直至任务结束; 

        Args:
            line (int, optional): 从倒数第line行开始读取. Defaults to 0.
            follow (bool, optional): 是否继续读取新数据直至满足轮询结束条件. Defaults to False.

        Yields:
            byte: 一行日志, 从前往后读取
        """
        tail_mode = True
        while True:
            if tail_mode:
                line_iter = self.tail(line=line, follow=follow)
            else:
                line_iter = self.more(follow=follow)
            total_byte = 0
            for line in line_iter:
                yield line
                total_byte += len(line)
            if total_byte == 0 and self._task_is_end:
                break
            if self._not_ready:
                time.sleep(self._retry_interval_not_ready)
                continue
            tail_mode = False