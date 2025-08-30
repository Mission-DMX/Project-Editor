"""Utility methods for filter channel name checking."""

from logging import getLogger

logger = getLogger(__name__)


def _rf(s: str) -> str:
    """Replace forbidden characters in sequence and channel names.

    Args:
        s: The name to process.

    Returns:
        The processed name.

    """
    if ":" in s or ";" in s:
        logger.warning("Replacing forbidden chars in sequencer key frame %s.", s)
        return s.replace(":", "_").replace(";", "_")
    return s
