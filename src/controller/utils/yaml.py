# coding=utf-8
from logging import getLogger

from ruamel import yaml

logger = getLogger(__file__)


def yaml_load(file_path: str) -> dict:
    """
    This method returns the content of the specified yaml file as a dictionary.

    :param file_path: The path to the YAML file to load
    :returns: The dictionary defined in the file or an empty one in case of any issue.
    """
    d = {}
    with open(file_path, 'r', encoding='UTF-8') as f:
        try:
            d = yaml.YAML(typ='safe').load(f.read())
        except Exception as e:
            logger.error("Failed to parse YAML file %s. %s", file_path, e)
            d = {}
    return d
