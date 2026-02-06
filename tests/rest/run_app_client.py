# python3 -m tests.rest.run_app_client client
"""
### 并发测试-HTTPServer
> python3 -m tests.rest.run_app daemon --use_threading_http_server=0
RestHttpServer use <class 'http.server.HTTPServer'>

> ab -n 4 -c 4 "http://127.0.0.1:8081/test/sleep2?interval=1"
Concurrency Level:      4
Time taken for tests:   4.020 seconds
Complete requests:      4
Failed requests:        0

### 并发测试-ThreadingHTTPServer
> python3 -m tests.rest.run_app daemon --use_threading_http_server=1
RestHttpServer use <class 'smart.rest.http.ThreadingHTTPServer.ThreadingHTTPServer'>

> ab -n 6 -c 5 "http://127.0.0.1:8081/test/sleep2?interval=1"
Concurrency Level:      5
Time taken for tests:   2.008 seconds
Complete requests:      6
Failed requests:        0

> ab -n 7 -c 6 "http://127.0.0.1:8081/test/sleep2?interval=1"
Benchmarking 127.0.0.1 (be patient)...apr_socket_recv: Connection reset by peer (54)
Total of 1 requests completed
"""

import fire, json, requests, time, queue

from smart.utils.dict import dict_safe_get


def test_client(port=8081):
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

    add_rst = __to_json_rst(requests.put(plan_api_baseurl, json={
        'content': 'First Plan is test app servce',
        'alarm': time.time() + 1
    }))

    print('\nadd_rst:', add_rst)

    plan_id = dict_safe_get(add_rst, ('data', 'id'))

    list_rst = __to_json_rst(requests.get(plan_api_baseurl+'/list'))
    print('\nlist_rst:', list_rst)

    # time.sleep(.5)
    # del_rst = __to_json_rst(requests.delete(plan_api_baseurl+'/'+str(plan_id)))
    # print('\ndel_rst:', del_rst)
    # list_rst = __to_json_rst(requests.get(plan_api_baseurl+'/list'))
    # print('\nlist_rst(after del):', list_rst)


def test_stress(interval:int=1, port:int=8081):
    test_api_baseurl = 'http://127.0.0.1:{port}/test/sleep'.format(
        port=str(port)
    )
    resp = requests.get(test_api_baseurl, params={
        "interval": interval
    })
    content = resp.content
    content = content.decode('utf8') if content is not None else None
    if content:
        resp_data = json.loads(content)
    else:
        resp_data = None
    print("resp_data: ", resp_data)


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)