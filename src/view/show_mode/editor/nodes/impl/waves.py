"""Wave forming filter nodes."""
from model.filter import Filter, FilterTypeEnumeration

from .trigonometics import TrigonometricNode

_WaveNode = TrigonometricNode


class SquareWaveNode(_WaveNode):
    """Filter to generate a square."""

    nodeName = "Square wave"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_WAVES_SQUARE, name=name)


class TriangleWaveNode(_WaveNode):
    """Filter to generate a triangle wave."""

    nodeName = "Triangle wave"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_WAVES_TRIANGLE, name=name)


class SawtoothWaveNode(_WaveNode):
    """Filter to generate a sawtooth wave."""

    nodeName = "Sawtooth wave"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_WAVES_SAWTOOTH, name=name)
