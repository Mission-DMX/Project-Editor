""""""
from NodeGraphQt import BaseNode, NodeGraph

from editor.editor_tab.filter_page.filter_graph.nodes.ports import BIT_16_PORT, BIT_8_PORT, COLOR_PORT, DOUBLE_PORT


def register_adapter_nodes(graph: NodeGraph) -> None:
    """
    Register all adapter nodes in a node graph.
    Args:
        graph: graph to register the nodes in
    """
    graph.register_node(Bit16ToBit8Node)
    graph.register_node(Bit16ToBoolNode)
    graph.register_node(Bit16ToFloat)
    graph.register_node(Bit8ToFloat)
    graph.register_node(ColorToRGBNode)
    graph.register_node(ColorToRGBWNode)
    graph.register_node(ColorToRGBWANode)
    graph.register_node(FloatToColorNode)
    graph.register_node(ColorToFloatNode)
    graph.register_node(FloatToRange)
    graph.register_node(FloatToBit8Range)
    graph.register_node(FloatToBit16Range)
    graph.register_node(Bit16ToRangeFloat)
    graph.register_node(Bit8ToRangeFloat)
    graph.register_node(CombineTwoBit8ToSingle16Bit)
    graph.register_node(MapBit8ToBit16)
    graph.register_node(ColorBrightnessMixinNode)


class Bit16ToBit8Node(BaseNode):
    """Adapter to convert a 16-bit value to an 8-bit value."""
    NODE_NAME = "16-Bit to 8-Bit Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_16_PORT)
        self.add_output("Value", data_type=BIT_8_PORT)


class Bit16ToBoolNode(BaseNode):
    """Adapter to convert a 16-bit value to a boolean value.
    If input is 0, output is 0, else 1."""
    NODE_NAME = "16-Bit to Bool Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_16_PORT)
        self.add_output("Value", data_type=BIT_8_PORT)


class Bit16ToFloat(BaseNode):
    """Adapter to convert a 16-bit value to a float value.
    If input is 0, output is 0, else 1."""
    NODE_NAME = "16-Bit to Float Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_16_PORT)
        self.add_output("Value", data_type=DOUBLE_PORT)


class Bit8ToFloat(BaseNode):
    """Adapter to convert a 8-bit value to a float value."""
    NODE_NAME = "8-Bit to Float Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_8_PORT)
        self.add_output("Value", data_type=DOUBLE_PORT)


class ColorToRGBNode(BaseNode):
    """Adapter to convert a Color value to RGB values."""
    NODE_NAME = "Color to RGB Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=COLOR_PORT)
        self.add_output("Red", data_type=BIT_8_PORT)
        self.add_output("Green", data_type=BIT_8_PORT)
        self.add_output("Blue", data_type=BIT_8_PORT)


class ColorToRGBWNode(BaseNode):
    """Adapter to convert a Color value to RGBW values."""
    NODE_NAME = "Color to RGBW Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=COLOR_PORT)
        self.add_output("Red", data_type=BIT_8_PORT)
        self.add_output("Green", data_type=BIT_8_PORT)
        self.add_output("Blue", data_type=BIT_8_PORT)
        self.add_output("White", data_type=BIT_8_PORT)


class ColorToRGBWANode(BaseNode):
    """Adapter to convert a Color value to RGBA values."""
    NODE_NAME = "Color to RGBWA Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=COLOR_PORT)
        self.add_output("Red", data_type=BIT_8_PORT)
        self.add_output("Green", data_type=BIT_8_PORT)
        self.add_output("Blue", data_type=BIT_8_PORT)
        self.add_output("White", data_type=BIT_8_PORT)
        self.add_output("Amber", data_type=BIT_8_PORT)


class FloatToColorNode(BaseNode):
    """Adapter to convert a float value to a Color value."""
    NODE_NAME = "Float to Color Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=DOUBLE_PORT)
        self.add_output("Color", data_type=COLOR_PORT)


class ColorToFloatNode(BaseNode):
    """Adapter to convert a color value to a float value."""
    NODE_NAME = "Color to Float Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=COLOR_PORT)
        self.add_output("Value", data_type=DOUBLE_PORT)


class FloatToRange(BaseNode):
    """Adapter to convert a float value to a range value."""
    NODE_NAME = "Float to Range Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=DOUBLE_PORT)
        self.add_output("Value", data_type=DOUBLE_PORT)
        self.add_spinbox("lower_bound_in", "lower_bound_in", 0.0, double=True)
        self.add_spinbox("upper_bound_in", "upper_bound_in", 1.0, double=True)
        self.add_spinbox("lower_bound_out", "lower_bound_out", 0.0, double=True)
        self.add_spinbox("upper_bound_out", "upper_bound_out", 1.0, double=True)  # TODO missing limit_range


class FloatToBit8Range(BaseNode):
    """Adapter to convert a float value to a range of 8-bit values."""
    NODE_NAME = "Float to 8-bit range Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=DOUBLE_PORT)
        self.add_output("Value", data_type=BIT_8_PORT)
        self.add_spinbox("upper_bound_out", "upper_bound_out", 255, min_value=0, max_value=255)


class FloatToBit16Range(BaseNode):
    """Adapter to convert a float value to a range of 16-bit values."""
    NODE_NAME = "Float to 8-bit range Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=DOUBLE_PORT)
        self.add_output("Value", data_type=BIT_16_PORT)
        self.add_spinbox("upper_bound_out", "upper_bound_out", 65535, min_value=0, max_value=65535)


class Bit16ToRangeFloat(BaseNode):
    """Adapter to convert a 16-bit value to a range of float values."""
    NODE_NAME = "16-Bit to float range Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_16_PORT)
        self.add_output("Value", data_type=DOUBLE_PORT)
        self.add_spinbox("upper_bound_in", "upper_bound_in", 65535, min_value=0, max_value=65535)


class Bit8ToRangeFloat(BaseNode):
    """Adapter to convert an 8-bit value to a range of float values."""
    NODE_NAME = "8-Bit to float range Adapter"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_8_PORT)
        self.add_output("Value", data_type=DOUBLE_PORT)
        self.add_spinbox("upper_bound_in", "upper_bound_in", 255, min_value=0, max_value=255)


class CombineTwoBit8ToSingle16Bit(BaseNode):
    """Adapter to combine two 8-bit values to a single 16-bit value."""
    NODE_NAME = "Dual 8bit to single 16bit"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("lower", data_type=BIT_8_PORT)
        self.add_input("upper", data_type=BIT_8_PORT)
        self.add_output("Value", data_type=BIT_16_PORT)


class MapBit8ToBit16(BaseNode):
    """Adapter to map a 8-bit value to a 16-bit value."""
    NODE_NAME = "Map 8bit to 16bit"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_8_PORT)
        self.add_output("Value", data_type=BIT_16_PORT)


class ColorBrightnessMixinNode(BaseNode):
    """Adapter to map a color with brightness to an 8-bit value."""
    NODE_NAME = "Color brightness Mixin"
    __identifier__ = "adapter"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("color_in", data_type=COLOR_PORT)
        self.add_input("brightness", data_type=BIT_8_PORT)
        self.add_output("Value", data_type=COLOR_PORT)
