# coding=utf-8
"""Constants filter nodes"""
from model import DataType

from view.show_mode.editor.nodes.base.filternode import FilterNode


class Constants8BitNode(FilterNode):
    """Filter to represent an 8 bit value."""
    nodeName = '8_bit_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=0, name=name, terminals={
            'value': {'io': 'out'}
        })

        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0"
        self.filter.out_data_types["value"] = DataType.DT_8_BIT
        self.filter.gui_update_keys["value"] = DataType.DT_8_BIT


class Constants16BitNode(FilterNode):
    """Filter to represent a 16 bit value."""
    nodeName = '16_bit_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=1, name=name, terminals={
            'value': {'io': 'out'}
        })

        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0"
        self.filter.out_data_types["value"] = DataType.DT_16_BIT
        self.filter.gui_update_keys["value"] = DataType.DT_16_BIT


class ConstantsFloatNode(FilterNode):
    """Filter to represent a float/double value."""
    nodeName = 'Float_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=2, name=name, terminals={
            'value': {'io': 'out'}
        })
        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0.0"
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["value"] = DataType.DT_DOUBLE


class ConstantsColorNode(FilterNode):
    """Filter to represent a color value.
    TODO specify color format
    """
    nodeName = 'Color_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=3, name=name, terminals={
            'value': {'io': 'out'}
        })
        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0,0,0"
        self.filter.out_data_types["value"] = DataType.DT_COLOR
        self.filter.gui_update_keys["value"] = DataType.DT_COLOR

class PanTiltConstant(FilterNode):
    """Filter to represent a pan/tilt position."""
    nodeName = 'PanTilt_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=-2, name=name, terminals={
            'value': {'io': 'out'}
        })
        try:
            self.filter.initial_parameters["pan"] = model.initial_parameters["pan"]
            self.filter.initial_parameters["tilt"] = model.initial_parameters["tilt"]
        except:
            self.filter.initial_parameters["pan"] = "0.0"
            self.filter.initial_parameters["tilt"] = "0.0"
        self.filter.out_data_types["pan"] = DataType.DT_16_BIT
        self.filter.out_data_types["tilt"] = DataType.DT_16_BIT
        self.filter.gui_update_keys["pan"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["tilt"] = DataType.DT_DOUBLE