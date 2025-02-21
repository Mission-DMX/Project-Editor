# coding=utf-8
"""Constants filter nodes"""
from PySide6.QtGui import QPainter

from model import DataType
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class Constants8BitNode(FilterNode):
    """Filter to represent an 8 bit value."""
    nodeName = '8_bit_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_8BIT, name=name, terminals={
            'value': {'io': 'out'}
        })

        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0"
        self.filter.out_data_types["value"] = DataType.DT_8_BIT
        self.filter.gui_update_keys["value"] = DataType.DT_8_BIT
        self.graphicsItem().additional_rendering_method = self._draw_preview

    def _draw_preview(self, p: QPainter):
        pass  # TODO


class Constants16BitNode(FilterNode):
    """Filter to represent a 16 bit value."""
    nodeName = '16_bit_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_16_BIT, name=name, terminals={
            'value': {'io': 'out'}
        })

        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0"
        self.filter.out_data_types["value"] = DataType.DT_16_BIT
        self.filter.gui_update_keys["value"] = DataType.DT_16_BIT
        self.graphicsItem().additional_rendering_method = self._draw_preview

    def _draw_preview(self, p: QPainter):
        pass  # TODO


class ConstantsFloatNode(FilterNode):
    """Filter to represent a float/double value."""
    nodeName = 'Float_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, name=name, terminals={
            'value': {'io': 'out'}
        })
        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0.0"
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["value"] = DataType.DT_DOUBLE
        self.graphicsItem().additional_rendering_method = self._draw_preview

    def _draw_preview(self, p: QPainter):
        pass  # TODO


class ConstantsColorNode(FilterNode):
    """Filter to represent a color value.
    TODO specify color format
    """
    nodeName = 'Color_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_COLOR, name=name, terminals={
            'value': {'io': 'out'}
        })
        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0,0,0"
        self.filter.out_data_types["value"] = DataType.DT_COLOR
        self.filter.gui_update_keys["value"] = DataType.DT_COLOR
        self.graphicsItem().additional_rendering_method = self._draw_preview

    def _draw_preview(self, p: QPainter):
        pass  # TODO


class PanTiltConstant(FilterNode):
    """Filter to represent a pan/tilt position."""
    nodeName = 'PanTilt_filter'

    def __init__(self, model, name):
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

    def _draw_preview(self, p: QPainter):
        pass  # TODO

    def setup_output_terminals(self):
        existing_output_keys = [k for k in self.outputs().keys()]
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
            'both' if eight_bit and sixteen_bit else '8bit' if eight_bit else '16bit'
        self.setup_output_terminals()
