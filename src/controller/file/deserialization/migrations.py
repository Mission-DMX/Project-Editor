# coding=utf-8
"""
This file contains methods to migrate a loading show file to a newer version
"""

from logging import getLogger

from model import Filter
from model.filter import FilterTypeEnumeration

logger = getLogger(__file__)


def replace_old_filter_configurations(f: Filter) -> Filter:
    """Replaces old filter representations if required.

    Certain filter representations have been replaced with their vFilter representation within the saved file.
    Furthermore, data formats inside the filters might change.
    In order to be capable of parsing old show files this method returns a new filter representation if required.

    :param f: The filter to check
    :returns: f if no modification was required or a new representation.
    """
    if f.filter_type == FilterTypeEnumeration.FILTER_TYPE_CUES:
        f.filter_type = int(FilterTypeEnumeration.VFILTER_CUES)
        logger.info("Replaced filter type of filter %s to become virtual.", f.filter_id)
    return f
