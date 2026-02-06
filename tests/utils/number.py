from smart.utils.number import *
from tests.utils import logger


def test_parse_float(float_vals=None):
    if float_vals is None:
        float_vals = [
            None,
            ".3",
            "1.2",
            "1.1f",
            "0",
            "a",
            "1e3",
            "-e-3",
            "-1e-3",
            "-.1e-3",
            "-2.1",
            "-.1"
        ]
    
    for val in float_vals:
        new_val = safe_parse_float(val)
        logger.info("%s %s -> %s %s", 
                type(val).__name__, val, 
                type(new_val).__name__, new_val)


if __name__ == "__main__":
    _d, component = dict(globals()).items(), {}
    for k, v in _d:
        if k.startswith('test_'):
            component[k] = v
            component[k[5:]] = v

    import fire
    fire.Fire(component)