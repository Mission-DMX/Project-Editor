# coding=utf-8
"""Trigonometric filter nodes"""
from model import DataType

from . import FilterNode


class TrigonometricNode(FilterNode):
    """Basic node class for sin, cos and tan"""
    def __init__(self, model, filter_type: int, name: str):
        super().__init__(model, filter_type, name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.in_data_types["value_in"] = DataType.DT_DOUBLE
        self.filter.in_data_types["factor_outer"] = DataType.DT_DOUBLE
        self.filter.in_data_types["factor_inner"] = DataType.DT_DOUBLE
        self.filter.in_data_types["phase"] = DataType.DT_DOUBLE
        self.filter.in_data_types["offset"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE


class TrigonometricSineNode(TrigonometricNode):
    """Filter to calculate sine value.
    value = factor_outer*sin((value_in+phase)*factor_inner) + offset
    """
    nodeName = 'sin'

    def __init__(self, model, name):
        super().__init__(model, filter_type=19, name=name)


class TrigonometricCosineNode(TrigonometricNode):
    """Filter to calculate cosine value.
    value = factor_outer*cos((value_in+phase)*factor_inner) + offset
    """
    nodeName = 'cos'

    def __init__(self, model, name):
        super().__init__(model, filter_type=20, name=name)


class TrigonometricTangentNode(TrigonometricNode):
    """Filter to calculate tangent value.
    value = factor_outer*tan((value_in+phase)*factor_inner) + offset
    """
    nodeName = 'tan'

    def __init__(self, model, name):
        super().__init__(model, filter_type=21, name=name)


class TrigonometricArcSinNode(TrigonometricNode):
    """Filter to calculate arcSine value.
    value = arcSin(value_in)
    """
    nodeName = 'arcsin'

    def __init__(self, model, name):
        super().__init__(model, filter_type=22, name=name)


class TrigonometricArcCosNode(TrigonometricNode):
    """Filter to calculate arcCosine value.
    value = arcCos(value_in)
    """
    nodeName = 'arccos'

    def __init__(self, model, name):
        super().__init__(model, filter_type=23, name=name)


class TrigonometricArcTanNode(TrigonometricNode):
    """Filter to calculate arcTangent value.
    value = arcTan(value_in)
    """
    nodeName = 'arctan'

    def __init__(self, model, name):
        super().__init__(model, filter_type=24, name=name)
