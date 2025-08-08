from logging import getLogger

logger = getLogger(__name__)


def _rf(s: str) -> str:
    """
    This method replaces for bidden characters in sequence and channel names.
    :param s: the name to process.
    :returns: The processed name.
    """
    if ":" in s or ";" in s:
        logger.warning("Replacing forbidden chars in sequencer key frame %s.", s)
        return s.replace(":", "_").replace(";", "_")
    return s
