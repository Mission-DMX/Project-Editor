"""Contains transfer function enum."""

from enum import Enum


class TransferFunction(Enum):
    """Enum describing transfer functions to a next key frame in a channel."""
    EDGE = "edg"
    LINEAR = "lin"
    SIGMOIDAL = "sig"
    EASE_IN = "e_i"
    EASE_OUT = "e_o"
