"""Trigonometric filter nodes."""
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class TrigonometricNode(FilterNode):
    """Basic node class for sin, cos and tan."""

    def __init__(self, model: Filter, filter_type: int, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, filter_type, name)
        self.channel_hints["phase"] = " [deg]"
        self.channel_hints["value_in"] = " [deg]"


class TrigonometricSineNode(TrigonometricNode):
    """Filter to calculate sine value.

    value = factor_outer*sin((value_in+phase)*factor_inner) + offset.
    """

    nodeName = "sin"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, filter_type=FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN, name=name)


class TrigonometricCosineNode(TrigonometricNode):
    """Filter to calculate cosine value.

    value = factor_outer*cos((value_in+phase)*factor_inner) + offset.
    """

    nodeName = "cos"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, filter_type=FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN, name=name)


class TrigonometricTangentNode(TrigonometricNode):
    """Filter to calculate tangent value.

    value = factor_outer*tan((value_in+phase)*factor_inner) + offset.
    """

    nodeName = "tan"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, filter_type=FilterTypeEnumeration.FILTER_TRIGONOMETRICS_TANGENT, name=name)


class TrigonometricArcSinNode(TrigonometricNode):
    """Filter to calculate arcSine value.

    value = arcSin(value_in).
    """

    nodeName = "arcsin"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, filter_type=FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCSIN, name=name)


class TrigonometricArcCosNode(TrigonometricNode):
    """Filter to calculate arcCosine value.

    value = arcCos(value_in).
    """

    nodeName: str = "arccos"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, filter_type=FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCCOSIN, name=name)


class TrigonometricArcTanNode(TrigonometricNode):
    """Filter to calculate arcTangent value.

    value = arcTan(value_in).
    """

    nodeName: str = "arctan"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, filter_type=FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCTANGENT, name=name)
