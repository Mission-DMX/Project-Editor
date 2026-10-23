"""Contains filter nodes for color manipulation."""

from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes import FilterNode


class ColorMixerHSVNode(FilterNode):
    """Node to mix colors based on their HSV representation."""

    nodeName = "Color Mixer HSV"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV, name=name)


class ColorMixerAdditiveRGBNode(FilterNode):
    """Node to mix colors based on their RGB representation using the additive algorithm."""

    nodeName = "Color Mixer Additive RGB"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_ADDITIVE_RGB, name=name)


class ColorMixerNormativeRGBNode(FilterNode):
    """Node to mix colors based on their RGB representation using the normative algorithm."""

    nodeName = "Color Mixer Normative RGB"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_NORMATIVE_RGB, name=name)


class ColorMixerVFilterNode(FilterNode):
    """Node to mix colors, using configurable virtual filter."""

    nodeName = "Color Mixer"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_COLOR_MIXER, name=name)


class ColorDirectorVFilterNode(FilterNode):
    """Filter node for color director virtual filter."""

    nodeName = "Color Director"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_COLORDIRECTOR, name=name)
