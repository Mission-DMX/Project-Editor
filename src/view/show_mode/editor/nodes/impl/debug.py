"""Debug filter nodes"""
from model import DataType
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class DebugNode(FilterNode):
    """Basic debug node"""

    def __init__(self, model: Filter, name: str, filter_type: int) -> None:
        super().__init__(model, filter_type, name, terminals={
            "value": {"io": "in"},
        })


class Debug8BitNode(DebugNode):
    """Filter to debug an 8 bit value.
    TODO implement visualization
    """
    node_name = "8 Bit Filter (Debug)"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_8BIT, name=name)
        self.filter.in_data_types["value"] = DataType.DT_8_BIT
        self.filter._configuration_supported = False


class Debug16BitNode(DebugNode):
    """Filter to debug a 16 bit value.
    TODO implement visualization
    """
    node_name = "16 Bit Filter (Debug)"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_16BIT, name=name)
        self.filter.in_data_types["value"] = DataType.DT_16_BIT
        self.filter._configuration_supported = False


class DebugFloatNode(DebugNode):
    """Filter to debug a float/double value.
    TODO implement visualization
    """
    node_name = "Float Filter (Debug)"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_FLOAT, name=name)
        self.filter.in_data_types["value"] = DataType.DT_DOUBLE
        self.filter._configuration_supported = False


class DebugColorNode(DebugNode):
    """Filter to debug a color value.
    TODO implement visualization
    """
    node_name = "Color Filter (Debug)"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_COLOR, name=name)
        self.filter.in_data_types["value"] = DataType.DT_COLOR
        self.filter._configuration_supported = False


class DebugRemote8BitNode(DebugNode):
    """Filter to debug an 8 bit value.
    TODO implement visualization
    """
    node_name = "8 Bit Filter (Debug, Remote)"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_REMOTE_DEBUG_8BIT, name=name)
        self.filter.in_data_types["value"] = DataType.DT_8_BIT
        self.filter._configuration_supported = False


class DebugRemote16BitNode(DebugNode):
    """Filter to debug a 16 bit value.
    TODO implement visualization
    """
    node_name = "16 Bit Filter (Debug, Remote)"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_REMOTE_DEBUG_16BIT, name=name)
        self.filter.in_data_types["value"] = DataType.DT_16_BIT
        self.filter._configuration_supported = False


class DebugRemoteFloatNode(DebugNode):
    """Filter to debug a float/double value.
    TODO implement visualization
    """
    node_name = "Float Filter (Debug, Remote)"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_REMOTE_DEBUG_FLOAT, name=name)
        self.filter.in_data_types["value"] = DataType.DT_DOUBLE
        self.filter._configuration_supported = False


class DebugRemoteColorNode(DebugNode):
    """Filter to debug a color value.
    TODO implement visualization
    """
    node_name = "Color Filter (Debug, Remote)"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_REMOTE_DEBUG_PIXEL, name=name)
        self.filter.in_data_types["value"] = DataType.DT_COLOR
        self.filter._configuration_supported = False
