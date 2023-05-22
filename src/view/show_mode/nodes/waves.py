# coding=utf-8
"""Wave forming filter nodes"""
from model import DataType
from . import FilterNode


class WaveNode(FilterNode):
    """Basic wave node"""
    def __init__(self, filter_type: int, name: str):
        super().__init__(filter_type, name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })

        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._in_value_types["factor_outer"] = DataType.DT_DOUBLE
        self._in_value_types["factor_inner"] = DataType.DT_DOUBLE
        self._in_value_types["phase"] = DataType.DT_DOUBLE
        self._in_value_types["offset"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class  SquareWaveNode(WaveNode):
    """Filter to generate a square."""
    nodeName = 'Square wave'

    def __init__(self, name):
        super().__init__(filter_type=25, name=name)
        self.addInput("length")
        self._in_value_types["length"] = DataType.DT_DOUBLE


class  TriangleWaveNode(WaveNode):
    """Filter to generate a triangle wave."""
    nodeName = 'Triangle wave'

    def __init__(self, name):
        super().__init__(filter_type=26, name=name)


class  SawtoothWaveNode(WaveNode):
    """Filter to generate a sawtooth wave."""
    nodeName = 'Sawtooth wave'

    def __init__(self, name):
        super().__init__(filter_type=27, name=name)
        self.addInput("length")
        self._in_value_types["length"] = DataType.DT_DOUBLE
