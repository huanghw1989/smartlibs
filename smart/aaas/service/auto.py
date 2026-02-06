import time
from smart.rest import RestRoute, RestService, RequestException
from smart.rest.base_req import HttpHeaderKey
from smart.rest.app.handler import RstHandlers, ErrHandlers
from smart.utils.dict import dict_find

from smart.aaas.base import AaasErrorCode
from smart.aaas.auto_manage import AutoManage
from smart.aaas.utils.task_info import AaasTaskInfoTool
from smart.utils.file.cat import FileCat

from smart.aaas.__logger import logger


rest = RestRoute()
err_handlers = ErrHandlers()


@rest.service('/auto')
class AutoService(RestService):
    @property
    def auto_manage(self) -> AutoManage:
        return getattr(self.app, 'auto_manage') if self.app else None

    @rest.request('run')
    def create_task(self, name=None, module=None, only_parse=None, rst_format=None, task_id=None, task_ns=None, **kwargs):
        module = module or self.json_param('module')
        name = name or self.json_param('name')
        only_parse = bool(only_parse)
        extra_configs = self.json_param('configs', {})
        bind_arg = self.json_param('bind_arg', {})
        state_hook = self.json_param('state_hook', None)
        other_run_opts = {**self.json_param('run_opts', {}), **kwargs}

        if not module: 
            raise RequestException("Miss param-module", AaasErrorCode.err_param)

        if not only_parse and not name: 
            raise RequestException("Miss param-name", AaasErrorCode.err_param)
        
        run_opts = {
            **other_run_opts,
            'extra': dict((k, v) for k, v in {
                'configs': extra_configs
            }.items() if v),
            'bind_arg': bind_arg,
        }

        if only_parse:
            return_dict = (not rst_format) or rst_format in ('json', 'raw')

            auto_obj_val = self.auto_manage.call_auto_run(module, name, {
                'only_parse': True,
                'rst_format': 'dict' if return_dict else rst_format,
                **run_opts
            })

            if not return_dict:
                if isinstance(auto_obj_val, str):
                    self.request.response_content(auto_obj_val)
                    return

            return auto_obj_val
        
        task_info = self.auto_manage.create_task(
            task_id = task_id, 
            task_ns = task_ns, 
            module = module, 
            name = name, 
            run_opts = run_opts,
            state_hook = state_hook)

        return task_info

    @rest.request('task_info')
    def get_task_info(self, task_id, task_ns=None):
        return self.auto_manage.get_task_info(task_id, task_ns)
    
    @rest.request('all_task')
    def get_all_task(self, task_ns=None):
        task_dict = self.auto_manage.get_task_dict(task_ns)

        return list(task_dict.values())

    @rest.request('all_task_ns')
    def get_all_task_ns(self):
        all_ns = list(self.auto_manage.all_task_ns())
        
        return all_ns
    
    @rest.request('end_task')
    def end_task(self, task_id, task_ns=None):
        task_dict = self.auto_manage.get_task_dict(task_ns)

        return self.auto_manage.end_task(task_dict, task_id)
    
    @rest.request('clean_task')
    def clean_task(self, task_info_ttl:int, task_ns=None):
        clean_task_ids = self.auto_manage.clean_task_dict(task_ns, task_info_ttl)

        return clean_task_ids
    
    @rest.request('task_log', rst_handler=RstHandlers.no_body, err_handler=err_handlers.header_mode)
    def task_log(self, task_id, task_ns=None, pool_interval:int=10, pool_line:int=10, log_offset:int=0, 
                tail_mode:bool=False, tail_line:int=0, tail_follow:bool=False):
        """获取任务日志(长轮询方式)
        tail_mode=False表示more模式, 从log_offset起读取pool_line行; 
        tail_mode=True表示tail模式, 先一次性向上读取tail_line行的数据(不受pool_line限制), 是否再向后读取由tail_follow参数控制; 
        如果tail_follow=True且上述逻辑返回的数据不足pool_line行, 则每隔一定时间间隔(缺省0.5)再向后读取数据，按完整行返回。

        Args:
            task_id (str): 任务ID
            task_ns (str, optional): 任务命名空间. Defaults to None.
            pool_interval (int, optional): 长轮询间隔. Defaults to 10.
            pool_line (int, optional): 长轮询每次获取行数. Defaults to 10.
            log_offset (int, optional): 日志文件的偏移量(单位byte), 仅当tail_mode=False有效. Defaults to 0.
            tail_mode (bool, optional): 是否从末尾读取文件, True为tail模式, False为more模式. Defaults to False.
            tail_line (int, optional): tail模式下, 从末尾向前读取tail_line行, 按正序返回. Defaults to 0.
            tail_follow (bool, optional): 达到文件末尾后, 是否向后按一定时间间隔(缺省0.5)读取行. Defaults to False.

        Raises:
            RequestException: 任务ID不存在
        """
        ts_begin = time.time()
        headers = {
            HttpHeaderKey.content_type:"text/plain"
        }
        set_resp_header = self.request.set_resp_header

        task_info_map = self.auto_manage.get_task_dict(task_ns)
        task_info = task_info_map.get(task_id)

        if not task_info:
            raise RequestException('no task')

        info_tool = AaasTaskInfoTool(task_info_map)
        stage_passed = info_tool.wait_stage(task_id, 'start', wait_end_ts=ts_begin+pool_interval)
        if not stage_passed:
            set_resp_header('AAAS-NOT-READY', '1')
            return
        # else:
        #     logger.debug("task_log %s start stage_passed", task_id)

        task_is_end = info_tool.check_stage_passed(task_id, 'end')
        if task_is_end:
            headers['AAAS-TASK-END'] = '1'
            tail_follow = False

        log_file_path = dict_find(task_info, ('task_log', 'file_path'))
        if not log_file_path:
            raise RequestException('miss task_log file')

        fp = open(log_file_path, mode='rb')
        self.request.context['after_complete_cb'] = lambda :(
            fp.close(), 
            # logger.debug("fp closed")
        )

        cat = FileCat(fp, text_mode=False)
        _line_iter = None
        if tail_mode:
            if not tail_line:
                cat.seek_tail()
            else:
                _line_iter = list(cat.tail(num_line=tail_line))
            _tail_n_offset = fp.tell()
            headers['AAAS-TAIL-N-OFFSET'] = str(_tail_n_offset)
        else:
            if log_offset:
                cat.seek(log_offset)
            _line_iter = cat.more(
                num_line=pool_line
            )

        def _out_iter_fn():
            i = 0
            if _line_iter:
                for line in _line_iter:
                    yield line
                    i += 1
                    # logger.debug("l-%s %s", i, line)
            if not tail_follow or i >= pool_line:
                return
            rest_time = pool_interval + ts_begin - time.time()
            if rest_time <= 0:
                return
            follow_expire_at = ts_begin + pool_interval
            follow_iter = cat.tail(
                num_line=0, num_byte=None,
                follow=True, follow_line_mode=True, follow_expire_at=follow_expire_at,
                follow_is_end_fn=lambda :info_tool.check_stage_passed(task_id, 'end')
            )
            for line in follow_iter:
                yield line
                i += 1
                # logger.debug("f-%s %s", i, line)
                if i >= pool_line:
                    break
            logger.debug("task_log end task=%s:%s, file: %s", task_ns or '', task_id, log_file_path)
        # wsgi模式, response_content不执行_line_iter_fn内的代码; 因此先结束本函数, 再执行_line_iter_fn内部的代码
        # daemon模式, response_content函数会执行_line_iter_fn
        # 所以, fp.close需要在after_complete调用
        self.request.response_content(_out_iter_fn(), headers=headers)
    
    @rest.hook.after_complete()
    def after_complete(self):
        _cb = self.request.context.get('after_complete_cb')
        if _cb:
            _cb()