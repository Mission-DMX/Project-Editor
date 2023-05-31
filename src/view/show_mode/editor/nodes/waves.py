# coding=utf-8
"""Wave forming filter nodes"""
from model import DataType
from .trigonometics import TrigonometricNode

_WaveNode = TrigonometricNode


class SquareWaveNode(_WaveNode):
    """Filter to generate a square."""
    nodeName = 'Square wave'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=25, name=name)
        self.addInput("length")
        self._in_value_types["length"] = DataType.DT_DOUBLE


class TriangleWaveNode(_WaveNode):
    """Filter to generate a triangle wave."""
    nodeName = 'Triangle wave'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=26, name=name)


class SawtoothWaveNode(_WaveNode):
    """Filter to generate a sawtooth wave."""
    nodeName = 'Sawtooth wave'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=27, name=name)
