"""Startup and general utility functions."""

import os
import sys
from logging import getLogger

logger = getLogger(__name__)


def resource_path(relative_path: str) -> str:
    """Resolve resource paths for the given installation method."""
    if "__compiled__" in globals():
        file_path = os.path.join(os.path.dirname(sys.argv[0]), relative_path)
    else:
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        file_path = os.path.join(base_path, relative_path)
    return file_path


def to_int(value: str, default: int) -> int:
    """Parse an integer configuration value, falling back to a default for malformed input."""
    try:
        return int(value)
    except ValueError:
        logger.warning("Malformed integer value %r, falling back to %d.", value, default)
        return default
