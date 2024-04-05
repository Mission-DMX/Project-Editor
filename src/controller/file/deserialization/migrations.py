"""
This file contains methods to migrate a loading show file to a newer version
"""
import logging

from model import Filter
from model.filter import FilterTypeEnumeration

from logging import getLogger
logger = getLogger(__file__)


def replace_old_filter_configurations(f: Filter) -> Filter:
    if f.filter_type == FilterTypeEnumeration.FILTER_TYPE_CUES:
        f._filter_type = int(FilterTypeEnumeration.VFILTER_CUES)
        logging.info("Replaced filter type of filter {} to become virtual.".format(f.filter_id))
    return f
