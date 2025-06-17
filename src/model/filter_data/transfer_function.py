from enum import Enum


class TransferFunction(Enum):
    EDGE = "edg"
    LINEAR = "lin"
    SIGMOIDAL = "sig"
    EASE_IN = "e_i"
    EASE_OUT = "e_o"
