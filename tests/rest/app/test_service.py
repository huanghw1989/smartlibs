# curl -v "http://127.0.0.1:8081/test/sleep2?interval=0.1" 
# curl -v --request POST "http://127.0.0.1:8081/test/post" --data-raw '{"a":1}'
# curl -v --request POST "http://127.0.0.1:8081/test/post" --data-raw '{"a":"啊"}'
import time
from smart.rest import RestRoute, RestService
from smart.rest.base import RequestException
from tests.rest import logger


rest = RestRoute()


@rest.service('/test')
class TestService(RestService):
    
    @rest.get('sleep')
    def sleep(self, interval:int):
        start_ts = time.time()
        time.sleep(interval)
        end_ts = time.time()

        return {
            'sleep': interval,
            'start_ts': start_ts,
            'end_ts': end_ts,
            'during': end_ts - start_ts
        }
    
    @rest.get('sleep2')
    def sleep2(self, interval:int):
        # logger.info("test sleep2 thread=%s", threading.current_thread().name)
        time.sleep(interval)

        return {
            'sleep': interval
        }

    @rest.get('mock_err')
    def mock_err(self, http_status:int=None, err_code:int=None):
        raise RequestException(msg='mock error', code=err_code or 8888, http_status=http_status)

    @rest.post('post')
    def post(self):
        a = self.json_param("a")
        b = self.json_param("b")
        return {
            "a": a,
            "b": b
        }
    
    @rest.hook.before_action()
    def before_action(self):
        self.request.context['ts_begin'] = time.time()

    @rest.hook.after_action()
    def after_action(self):
        _ts_begin = self.request.context['ts_begin']
        if not _ts_begin:
            return
        ts_during = time.time() - _ts_begin
        logger.debug("request cost %s second", ts_during)

    @rest.hook.after_complete()
    def after_complete(self):
        logger.debug("request %s after_complete", self.request.path)