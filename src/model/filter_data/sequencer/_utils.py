from logging import getLogger

logger = getLogger(__file__)


def _rf(s: str) -> str:
    if ":" in s or ";" in s:
        logger.warning("Replacing forbidden chars in sequencer key frame {}.", s)
        return s.replace(":", "_").replace(";", "_")
    else:
        return s
