# python3 -m tests.rest.run_app daemon
import time, requests, json, queue

from concurrent.futures.thread import ThreadPoolExecutor
from http.server import HTTPServer

from smart.rest import RestServiceApplication, BootConfig
from smart.utils import dict_safe_get


from .app.notify_manage import NotifyManage

from .TestRestApp import TestRestApp

# boot = BootConfig()

# @boot.crond()
# @boot.service('app.*')
# class TestRestApp(RestServiceApplication):
#     pass


def test_daemon(port=8081, use_threading_http_server=True):
    other_kwargs = {}
    if not use_threading_http_server:
        other_kwargs['http_server'] = HTTPServer

    app:RestServiceApplication = TestRestApp(
        port=port, **other_kwargs
    )
    app.daemon()


def test_rest_app(port=8081, use_threading_http_server=True):
    pool = ThreadPoolExecutor(max_workers=2)
    other_kwargs = {}
    if not use_threading_http_server:
        other_kwargs['http_server'] = HTTPServer

    app:RestServiceApplication = TestRestApp(
        port=port, **other_kwargs
    )

    app_future = pool.submit(lambda : app.daemon())

    plan_api_baseurl = 'http://127.0.0.1:{port}/plan'.format(
        port=str(port)
    )

    def __to_json_rst(resp):
        content = resp.content
        content = content.decode('utf8') if content is not None else None
        if content:
            return json.loads(content)
        else:
            return None

    def __test_plan_service():
        add_rst = __to_json_rst(requests.put(plan_api_baseurl, json={
            'content': 'First Plan is test app servce',
            'alarm': time.time() + 1
        }))

        print('\nadd_rst:', add_rst)

        plan_id = dict_safe_get(add_rst, ('data', 'id'))

        list_rst = __to_json_rst(requests.get(plan_api_baseurl+'/list'))
        print('\nlist_rst:', list_rst)

        if plan_id is not None:
            # Wait alarm notify test
            try:
                # plan = NotifyManage.notify_plans.get(block=True, timeout=10)
                plan = NotifyManage.notify_plans.get(block=True, timeout=10)
                print('\nnotify_plan:', plan)
            except queue.Empty:
                print('\nnotify_plans empty')

            del_rst = __to_json_rst(requests.delete(plan_api_baseurl+'/'+str(plan_id)))
            print('\ndel_rst:', del_rst)
            list_rst = __to_json_rst(requests.get(plan_api_baseurl+'/list'))
            print('\nlist_rst(after del):', list_rst)
            time.sleep(.5)
            
        return True
        

    def __done_test(*args):
        print('enter __done_test', args)
        app.shutdown()
        print('app has shutdown')
        print('test_rest_app done')
    
    time.sleep(1)
    test_future = pool.submit(__test_plan_service)
    test_future.add_done_callback(__done_test)

    print('test_future rst:', test_future.result())
    print('app_future rst:', app_future.result())


def test_rest_app_cron(port = 8081):
    app:RestServiceApplication = TestRestApp(
        port=port
    )

    from .app.plan_service import PlanService
    plan_service = PlanService()

    main_process = app.start_crond()



if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)