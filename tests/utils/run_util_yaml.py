"""
Run Example: 
python3 -m tests.utils.run_util_yaml test_yaml_load
python3 -m tests.utils.run_util_yaml test_yaml_load_file
"""
import json

from smart.utils import yaml_load, yaml_load_file


def test_yaml_load():
    document = """
    a: 1
    b:
      c: 3
      d: 4
    e.e:
      - a
      - 5
      - '6'
    """
    print(yaml_load(document))


def test_yaml_load_file(file='tests/utils/test_yml/a.b.yml'):
    cfg_obj = yaml_load_file(file)
    print(json.dumps(cfg_obj, indent=2))
    for key, item in cfg_obj.get("configs", {}).items():
        print("{}: {}, {}".format(key, type(item), item))


if __name__ == "__main__":
    import fire
    fire.Fire({
        k: v
        for k, v in globals().items()
        if k.startswith('test_')
    })