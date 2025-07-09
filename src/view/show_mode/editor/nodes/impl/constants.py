"""Constants filter nodes"""
from logging import getLogger

from PySide6.QtGui import QBrush, QColor, QFontMetrics, QPainter

from model import ColorHSI, DataType
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode

logger = getLogger(__file__)

_text_brush = QBrush(QColor(30, 30, 30, 255))
_value_box_brush = QBrush(QColor(128, 128, 128, 150))


class TextPreviewRendererMixin(FilterNode):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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
    nodeName = "8_bit_filter"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_8BIT, name=name, terminals={
            "value": {"io": "out"}
        })

        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0"
        self.filter.out_data_types["value"] = DataType.DT_8_BIT
        self.filter.gui_update_keys["value"] = DataType.DT_8_BIT

    def update_node_after_settings_changed(self):
        try:
            self.filter.initial_parameters["value"] = str(
                max(min(int(self.filter.initial_parameters["value"]), 255), 0))
        except ValueError as e:
            logger.error("Error while checking entered value. %s", e)
            self.filter.initial_parameters["value"] = "0"


class Constants16BitNode(TextPreviewRendererMixin):
    """Filter to represent a 16 bit value."""
    nodeName = "16_bit_filter"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_16_BIT, name=name, terminals={
            "value": {"io": "out"}
        })

        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0"
        self.filter.out_data_types["value"] = DataType.DT_16_BIT
        self.filter.gui_update_keys["value"] = DataType.DT_16_BIT

    def update_node_after_settings_changed(self):
        try:
            self.filter.initial_parameters["value"] = str(
                max(min(int(self.filter.initial_parameters["value"]), 65565), 0))
        except ValueError as e:
            logger.error("Error while checking entered value. %s", e)
            self.filter.initial_parameters["value"] = "0"


class ConstantsFloatNode(TextPreviewRendererMixin):
    """Filter to represent a float/double value."""
    nodeName = "Float_filter"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, name=name, terminals={
            "value": {"io": "out"}
        })
        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0.0"
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["value"] = DataType.DT_DOUBLE
        self.graphicsItem().additional_rendering_method = self._draw_preview

    def update_node_after_settings_changed(self):
        try:
            self.filter.initial_parameters["value"] = str(
                float(self.filter.initial_parameters["value"]))
        except ValueError as e:
            logger.error("Error while checking entered value. %s", e)
            self.filter.initial_parameters["value"] = "0.0"


class ConstantsColorNode(FilterNode):
    """Filter to represent a color value.
    TODO specify color format
    """
    nodeName = "Color_filter"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_COLOR, name=name, terminals={
            "value": {"io": "out"}
        })
        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0,0,0"
        self.filter.out_data_types["value"] = DataType.DT_COLOR
        self.filter.gui_update_keys["value"] = DataType.DT_COLOR
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

    def update_node_after_settings_changed(self):
        try:
            self._color_brush = QBrush(ColorHSI.from_filter_str(self.filter.initial_parameters["value"]).to_qt_color())
        except ValueError as e:
            logger.error("Error while checking entered value. %s", e)
            self.filter.initial_parameters["value"] = "0,0,0"


class PanTiltConstant(FilterNode):
    """Filter to represent a pan/tilt position."""
    nodeName = "PanTilt_filter"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_POSITION_CONSTANT, name=name,
                         terminals={}, allowAddOutput=True)
        try:
            self.filter.initial_parameters["pan"] = model.initial_parameters["pan"]
        except:
            self.filter.initial_parameters["pan"] = "0.5"
        try:
            self.filter.initial_parameters["tilt"] = model.initial_parameters["tilt"]
        except:
            self.filter.initial_parameters["tilt"] = "0.5"
        self.filter.out_data_types["pan16bit"] = DataType.DT_16_BIT
        self.filter.out_data_types["tilt16bit"] = DataType.DT_16_BIT
        self.filter.out_data_types["pan8bit"] = DataType.DT_8_BIT
        self.filter.out_data_types["tilt8bit"] = DataType.DT_8_BIT
        try:
            outputs_from_file = model.filter_configurations["outputs"]
            self.filter.filter_configurations["outputs"] = outputs_from_file
        except:
            self.filter.filter_configurations["outputs"] = "16bit"
        self.setup_output_terminals()
        self.filter.gui_update_keys["pan"] = DataType.DT_DOUBLE
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

    def setup_output_terminals(self):
        existing_output_keys = list(self.outputs().keys())
        outputs = self.filter.filter_configurations["outputs"]
        match outputs:
            case "both":
                if "pan8bit" not in existing_output_keys:
                    self.addOutput("pan8bit")
                if "tilt8bit" not in existing_output_keys:
                    self.addOutput("tilt8bit")
                if "pan16bit" not in existing_output_keys:
                    self.addOutput("pan16bit")
                if "tilt16bit" not in existing_output_keys:
                    self.addOutput("tilt16bit")
            case "8bit":
                if "pan8bit" not in existing_output_keys:
                    self.addOutput("pan8bit")
                if "tilt8bit" not in existing_output_keys:
                    self.addOutput("tilt8bit")
                if "pan16bit" in existing_output_keys:
                    self.removeTerminal("pan16bit")
                if "tilt16bit" in existing_output_keys:
                    self.removeTerminal("tilt16bit")
            case "16bit":
                if "pan8bit" in existing_output_keys:
                    self.removeTerminal("pan8bit")
                if "tilt8bit" in existing_output_keys:
                    self.removeTerminal("tilt8bit")
                if "pan16bit" not in existing_output_keys:
                    self.addOutput("pan16bit")
                if "tilt16bit" not in existing_output_keys:
                    self.addOutput("tilt16bit")

    def outputs_changed(self, eight_bit: bool, sixteen_bit: bool):
        self.filter.filter_configurations["outputs"] = \
            "both" if eight_bit and sixteen_bit else "8bit" if eight_bit else "16bit"
        self.setup_output_terminals()
