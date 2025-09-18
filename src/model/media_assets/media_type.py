"""Module contains MediaType enum."""

from enum import Enum


class MediaType(Enum):
    """Enum provides the distinguished media types."""

    TEXT = 0
    IMAGE = 1
    VIDEO = 2
    AUDIO = 3
    MODEL_3D = 4
