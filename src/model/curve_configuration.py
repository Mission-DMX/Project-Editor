from enum import IntFlag


class BaseCurve(IntFlag):
    """This enum defines which parts should be present in the wave. If multiple apply, they'll be added or multiplied,
    depending on the accumulation selection."""
    NONE = 0
    SIN = 1
    COS = 2
    TAN = 4
    ARC_SIN = 8
    ARC_COS = 16
    ARC_TAN = 32
    SAWTOOTH = 64
    RECT = 128
    TRIANGLE = 256


class CurveConfiguration:

    def __init__(self):
        self.selected_features: BaseCurve = BaseCurve.NONE
        self.append_features_using_addition: bool = False
        self.base_phase: float = 0.0
        self.base_amplitude: float = 1.0

    def serialize(self) -> str:
        pass  # TODO implement

    @classmethod
    def from_str(cls, config: str) -> "CurveConfiguration":
        cc = CurveConfiguration()

        return cc
