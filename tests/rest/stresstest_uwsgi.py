"""
run server:
> uwsgi --http :9090 --wsgi-file tests/rest/stresstest_uwsgi.py --master --processes 4 --threads 2

debug server:
> REMOTE_DEBUG=1 uwsgi --http :9090 --wsgi-file tests/rest/stresstest_uwsgi.py
> curl http://127.0.0.1:9090/

ab test:
> ab -n 1000 -c 100 http://127.0.0.1:9090/
"""
from smart.utils import remote_debug

def application(env, start_response):
    remote_debug.enable_by_env()
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"Hello World"]