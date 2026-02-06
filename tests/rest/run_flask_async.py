# pip install 'flask[async]'
# python3.10 tests/rest/run_flask_async.py
"""
并发测试: ab -n 50 -c 10 "http://localhost:8080/test?sleep=1"
Concurrency Level:      10
Time taken for tests:   6.048 seconds
Complete requests:      50
Failed requests:        0
Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       0
Processing:  1002 1007   4.0   1005    1016
Waiting:     1002 1006   3.7   1005    1016
Total:       1002 1007   4.0   1005    1016
"""

import time, asyncio

from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/test", methods=["GET"])
async def test_sleep():
    begin_ts = time.time()
    sleep = int(request.args.get("sleep", 0.5))
    await asyncio.sleep(sleep)
    end_ts = time.time()
    print("test ", [end_ts-begin_ts, begin_ts, end_ts])
    return {
        "sleep": sleep,
        # "ts": [end_ts-begin_ts, begin_ts, end_ts]
    }


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080)