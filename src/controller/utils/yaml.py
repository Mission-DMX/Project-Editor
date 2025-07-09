"""YAML handler"""
from logging import getLogger

from ruamel import yaml
from ruamel.yaml import YAMLError

logger = getLogger(__name__)


def yaml_load(file_path: str) -> dict:
    """
    This method returns the content of the specified YAML file as a dictionary.

    :param file_path: The path to the YAML file to load
    :returns: The dictionary defined in the file or an empty one in case of any issue.
    """
    d = {}
    with open(file_path, encoding="UTF-8") as f:
        try:
            d = yaml.YAML(typ="safe").load(f.read())
        except YAMLError as e:
            logger.error("Failed to parse YAML file %s. %s", file_path, e)
            d = {}
    return d
