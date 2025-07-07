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
    """
    This class defines curves described using the mathematical primitives provided by fish.
    It cannot be transferred to fish directly (yet) but is used across different components of
    the gui that interact with fish. Most notably, it is used by the effects stack to define curves for effects.
    """

    def __init__(self):
        self.frequencies: dict[BaseCurve, float] = {}
        self.amplitudes: dict[BaseCurve, float] = {}
        self.offsets: dict[BaseCurve, float] = {}
        for curve in [BaseCurve(2 ** c) for c in range(9)]:
            self.frequencies[curve] = 1.0
            self.amplitudes[curve] = 1.0
            self.offsets[curve] = 0.0
        self.selected_features: BaseCurve = BaseCurve.NONE
        self.append_features_using_addition: bool = False
        self.base_phase: float = 0.0
        self.base_amplitude: float = 1.0

    def serialize(self) -> str:
        """
        This method serializes the configuration into a format for being saved inside strings in the showfile.
        It does not necessarily represent a format that components of fish can understand.

        :returns: A string representing the configuration
        """
        return ";".join([
            "1",  # Opset
            str(self.selected_features),
            str(self.base_phase),
            str(self.base_amplitude),
            "true" if self.append_features_using_addition else "false",
            ",".join([str(k) + ":" + str(v) for k, v in self.frequencies.items()]),
            ",".join([str(k) + ":" + str(v) for k, v in self.amplitudes.items()]),
            ",".join([str(k) + ":" + str(v) for k, v in self.offsets.items()])
        ])

    @classmethod
    def from_str(cls, config: str) -> "CurveConfiguration":
        """
        This method deserializes this class using the format provided by the serialize function.

        :param config: The representation of the object as a serialized string.
        :returns: a new CurveConfiguration object
        """
        cc = CurveConfiguration()
        if config is None or len(config) == 0:
            return cc
        config = config.split(';')
        opset = int(config[0])
        cc.selected_features = BaseCurve(int(config[1]))
        cc.base_phase = float(config[2])
        cc.base_amplitude = float(config[3])
        cc.append_features_using_addition = config[4] == "true"

        def decode_common_props(target: dict[BaseCurve, float], source: str):
            for entry in source.split(','):
                k, v = entry.split(':')
                k = BaseCurve(int(k))
                v = float(v)
                target[k] = v
        decode_common_props(cc.frequencies, config[5])
        decode_common_props(cc.amplitudes, config[6])

        if opset > 0:
            decode_common_props(cc.offsets, config[7])
        return cc
