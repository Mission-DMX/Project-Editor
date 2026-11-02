"""Constants filter nodes."""
from logging import getLogger
from typing import override

from PySide6.QtGui import QBrush, QColor, QFontMetrics, QPainter

from model import Scene
from model.color_hsi import ColorHSI
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode

logger = getLogger(__name__)

_text_brush = QBrush(QColor(30, 30, 30, 255))
_value_box_brush = QBrush(QColor(128, 128, 128, 150))


class TextPreviewRendererMixin(FilterNode):
    """Mixin to render text based previews in filter nodes."""

    def __init__(self, model: Filter | Scene,
                 filter_type: int,
                 name: str,
                 terminals: dict[str, dict[str, str]] | None = None,
                 allow_add_input: bool = False,
                 allow_add_output: bool = False) -> None:
        """Initialize."""
        super().__init__(model, filter_type, name, terminals, allow_add_input, allow_add_output)
        self.graphicsItem().additional_rendering_method = self._draw_preview

    def _draw_preview(self, p: QPainter) -> None:
        value_str = str(self.filter.initial_parameters.get("value"))
        fm: QFontMetrics = p.fontMetrics()
        sheight = fm.height()
        slen = fm.horizontalAdvance(value_str)
        br = self.graphicsItem().boundingRect()
        p.scale(1.0, 1.0)
        y = (br.height() - sheight - 12) / 0.25
        x = ((br.width() / 2) / 0.25) - (slen / 2) - 10
        p.setBrush(_value_box_brush)
        p.drawRect(x, y, slen + 6, sheight + 6)
        p.setBrush(_text_brush)
        p.drawText(x + 3, y + sheight, value_str)


class Constants8BitNode(TextPreviewRendererMixin):
    """Filter to represent an 8 bit value."""

    nodeName = "8_bit_filter"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_8BIT, name=name)

    @override
    def update_node_after_settings_changed(self) -> None:
        try:
            self.filter.initial_parameters["value"] = str(
                max(min(int(self.filter.initial_parameters["value"]), 255), 0))
        except ValueError as e:
            logger.exception("Error while checking entered value. %s", e)
            self.filter.initial_parameters["value"] = "0"


class Constants16BitNode(TextPreviewRendererMixin):
    """Filter to represent a 16 bit value."""

    nodeName = "16_bit_filter"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_16_BIT, name=name)

    @override
    def update_node_after_settings_changed(self) -> None:
        try:
            self.filter.initial_parameters["value"] = str(
                max(min(int(self.filter.initial_parameters["value"]), 65565), 0))
        except ValueError as e:
            logger.exception("Error while checking entered value. %s", e)
            self.filter.initial_parameters["value"] = "0"


class ConstantsFloatNode(TextPreviewRendererMixin):
    """Filter to represent a float/double value."""

    nodeName = "Float_filter"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, name=name)

    @override
    def update_node_after_settings_changed(self) -> None:
        try:
            self.filter.initial_parameters["value"] = str(
                float(self.filter.initial_parameters["value"]))
        except ValueError as e:
            logger.exception("Error while checking entered value. %s", e)
            self.filter.initial_parameters["value"] = "0.0"


class ConstantsColorNode(FilterNode):
    """Filter to represent a color value.

    Colors are stored as "h,s,i" where h is a float in [0,360], s and i are float in [0,1].

    """

    nodeName = "Color_filter"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_COLOR, name=name)
        self.graphicsItem().additional_rendering_method = self._draw_preview
        self._color_brush = QBrush(ColorHSI.from_filter_str(self.filter.initial_parameters["value"]).to_qt_color())

    def _draw_preview(self, p: QPainter) -> None:
        p.setBrush(_value_box_brush)
        br = self.graphicsItem().boundingRect()
        p.scale(1.0, 1.0)
        y = (br.height() - 26 - 12) / 0.25
        x = (br.width() / 2 - 13) / 0.25
        p.drawRect(x, y, 20 + 6, 20 + 6)
        p.setBrush(self._color_brush)
        p.drawRect(x + 3, y + 3, 20, 20)

    @override
    def update_node_after_settings_changed(self) -> None:
        try:
            self._color_brush = QBrush(ColorHSI.from_filter_str(self.filter.initial_parameters["value"]).to_qt_color())
        except ValueError as e:
            logger.exception("Error while checking entered value. %s", e)
            self.filter.initial_parameters["value"] = "0,0,0"


class PanTiltConstant(FilterNode):
    """Filter to represent a pan/tilt position."""

    nodeName = "PanTilt_filter"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(
            model=model, filter_type=FilterTypeEnumeration.VFILTER_POSITION_CONSTANT, name=name, allow_add_output=True
        )
        self.graphicsItem().additional_rendering_method = self._draw_preview

    def _draw_preview(self, p: QPainter) -> None:
        value_pan_str = "Pan: " + str(self.filter.initial_parameters.get("pan"))
        value_tilt_str = "Tilt: " + str(self.filter.initial_parameters.get("tilt"))
        fm: QFontMetrics = p.fontMetrics()
        sheight = fm.height() * 2 + 6
        slen = max(fm.horizontalAdvance(value_pan_str), fm.horizontalAdvance(value_tilt_str))
        br = self.graphicsItem().boundingRect()
        p.scale(1.0, 1.0)
        y = (br.height() - sheight - 12) / 0.25
        x = (br.width() / 10)
        p.setBrush(_value_box_brush)
        p.drawRect(x, y, slen + 6, sheight + 6)
        p.setBrush(_text_brush)
        p.drawText(x + 3, y + fm.height() + 3, value_pan_str)
        p.drawText(x + 3, y + sheight, value_tilt_str)
