from smart.utils.retry import *
import random


@retry_fn(3)
def test_foo(prob:float=0.5):
    logger_utils.info("test_foo begin")
    r = random.random()
    if r < prob:
        raise Exception("foo error {} {}".format(prob, r))
    else:
        logger_utils.info("test_foo random num={}".format(r))
        return r

class TestRetryFoo:
    DEFAULT_PROB = 0.5

    @classmethod
    @retry_fn(3)
    def foo(self, prob=None):
        prob = prob if prob is not None else self.DEFAULT_PROB
        r = random.random()
        if r < prob:
            raise Exception("TestRetryFoo.foo error {} {}".format(prob, r))
        else:
            logger_utils.info("TestRetryFoo.foo random num={}".format(r))
            return r

def test_foo_cls(prob:float=None):
    foo = TestRetryFoo()
    return foo.foo(prob=prob)


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)