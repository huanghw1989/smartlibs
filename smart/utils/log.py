import logging, os
import logging.config

from .__logger import logger_utils
from .yaml import yaml_load_file
from .dict import dict_find, dict_safe_set
from .template import DictTemplateParser


def parse_logging_config(config_dict:dict):
    handlers = dict_find(config_dict, 'handlers')
    if not handlers:
        return config_dict
    parser = DictTemplateParser(handlers)
    pid = os.getpid()
    new_handlers = parser.parse_pattern_key(
        extra_envs={
            'pid': str(pid)
        },
        parse_deep=2
    ).get_value()
    dict_safe_set(config_dict, 'handlers', new_handlers)
    return config_dict


def auto_load_logging_config(base_dir=None, file_name='logging.yml'):
    if base_dir is None:
        base_dir = os.getcwd()

    curr_dir = base_dir

    while True:
        log_path = os.path.join(curr_dir, file_name)

        if os.path.exists(log_path):

            dict_config = parse_logging_config(
                yaml_load_file(log_path)
            )
            logging.config.dictConfig(dict_config)
            # print('logging dictConfig', dict_config)
            # logging.config.fileConfig(log_path)
            logger_utils.debug('Use logging config: %s', log_path)

            return True
        else:

            parent_dir = os.path.dirname(curr_dir)

            if not parent_dir or parent_dir == curr_dir:
                break

            curr_dir = parent_dir
            
    return False



def set_default_logging_config(level=logging.INFO):
    logging.basicConfig(
        level = level, 
        format = '%(asctime)s %(levelname)s %(message)s')