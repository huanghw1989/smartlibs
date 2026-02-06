"""
### server
# multithread
> uwsgi --http :8081 --module "tests.rest.run_wsgi:create_app()"  --master --processes 1 --threads 10

# Debug Mode
> REMOTE_DEBUG=1 uwsgi --http :8081 --module "tests.rest.run_wsgi:create_app()"

### client
call api:
> curl http://127.0.0.1:8081/plan/list

python3 -m tests.rest.run_app_client client

## 并发测试: ab -n 50 -c 10 "http://localhost:8081/test/sleep2?interval=1"
Concurrency Level:      10
Time taken for tests:   6.089 seconds
Complete requests:      50
Failed requests:        0
Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.4      0       2
Processing:  1001 1012  16.6   1005    1059
Waiting:     1001 1011  16.6   1005    1059
Total:       1001 1012  16.9   1005    1061
"""

from smart.utils import remote_debug

remote_debug.enable_by_env()

from tests.rest.TestRestApp import TestRestApp
# from .TestRestApp import TestRestApp

# from smart.rest import RestServiceApplication, BootConfig
# boot = BootConfig()

# @boot.crond()
# @boot.service('.app.*')
# class TestRestApp(RestServiceApplication):
#     pass



def create_app():
    _app = TestRestApp()
    _app.start(wsgi_mode=True)
    return _app.wsgi