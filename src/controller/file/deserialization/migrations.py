"""Methods to migrate a loading show file to a newer version."""

from logging import getLogger

from model import Filter
from model.filter import FilterTypeEnumeration

logger = getLogger(__name__)


def replace_old_filter_configurations(f: Filter) -> tuple[Filter, bool]:
    """Replace outdated filter representations if necessary.

    Some filter representations may have been replaced with their vFilter
    counterparts in saved files. Additionally, data formats inside filters
    might change over time. To ensure backward compatibility when parsing
    old show files, this method returns an updated filter representation if
    needed.

    Args:
        f: The filter to check.

    Returns:
        The original filter if no modification was required, or a new
        updated representation. Also True if a migration happened.

    """
    migration_happened: bool = False
    if f.filter_type == FilterTypeEnumeration.FILTER_TYPE_CUES:
        f.filter_type = int(FilterTypeEnumeration.VFILTER_CUES)
        logger.info("Replaced filter type of filter %s to become virtual on next load. Reloading is advised.",
                    f.filter_id)
        migration_happened = True
    if f.filter_type in [
        FilterTypeEnumeration.FILTER_FADER_RAW,
        FilterTypeEnumeration.FILTER_FADER_HSI,
        FilterTypeEnumeration.FILTER_FADER_HSIA,
        FilterTypeEnumeration.FILTER_FADER_HSIU,
        FilterTypeEnumeration.FILTER_FADER_HSIAU,
    ]:
        f.filter_type = int(int(f.filter_type) * -1)
        logger.info("Replaced filter type of filter %s to become virtual on next load. Reloading is advised",
                    f.filter_id)
        migration_happened = True
    return f, migration_happened
