**---use claude sonnet 4.6---**
- smart/rest/app/crond.py `python3 -m smart.aaas.run`运行报错：
    File "smartlibs/smart/rest/app/crond.py", line 170, in run
        self.loop_task = loop.run_until_complete(asyncio.wait(
    File "/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/asyncio/base_events.py", line 687, in run_until_complete
        return future.result()
    File "/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/asyncio/tasks.py", line 461, in wait
        raise TypeError("Passing coroutines is forbidden, use tasks explicitly.")
    TypeError: Passing coroutines is forbidden, use tasks explicitly.

  - 上面的改动是否兼容python3.8 - python3.10

  - 运行会有warning：
    smartlibs/smart/__init__.py:4: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.

    __import__('pkg_resources').declare_namespace(__name__)

