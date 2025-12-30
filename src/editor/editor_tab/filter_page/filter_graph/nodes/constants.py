"""Constant nodes for the Node Editor."""
from NodeGraphQt import NodeGraph

from editor.editor_tab.filter_page.filter_graph.nodes.ports import BIT_16_PORT, BIT_8_PORT, DOUBLE_PORT
from editor.editor_tab.filter_page.filter_graph.nodes.registered_base_node import RegisteredBaseNode


def register_constant_nodes(graph: NodeGraph) -> None:
    """
    Register all constant nodes in a node graph.
    Args:
        graph: the node graph to register the nodes in.

    """
    graph.register_node(Bit8Node)
    graph.register_node(Bit16Node)
    graph.register_node(FloatNode)


class Bit8Node(RegisteredBaseNode):
    """Filter to represent an 8-bit value."""
    NODE_NAME = "8-Bit Filter"
    __identifier__ = "constant"
    __representation__ = 0

    def __init__(self) -> None:
        super().__init__()
        self.add_output("Value", data_type=BIT_8_PORT)
        self.add_spinbox("value", "value", 0, 0, 255)


class Bit16Node(RegisteredBaseNode):
    """Filter to represent a 16-bit value."""
    NODE_NAME = "16-Bit Filter"
    __identifier__ = "constant"
    __representation__ = 1

    def __init__(self) -> None:
        super().__init__()
        self.add_output("Value", data_type=BIT_16_PORT)
        self.add_spinbox("value", "value", 0, 0, 65535)


class FloatNode(RegisteredBaseNode):
    """Filter to represent a float/double value."""
    NODE_NAME = "Float Filter"
    __identifier__ = "constant"
    __representation__ = 2

    def __init__(self) -> None:
        super().__init__()
        self.add_output("Value", data_type=DOUBLE_PORT)
        self.add_spinbox("value", "value", 0.0, double=True)

# class ColorNode(RegisteredBaseNode):
#    """Filter to represent a color value.
#    TODO specify color format
#    """
#    NODE_NAME = "Float Filter"
#    __identifier__ = "constant"
#    __representation__ = 3
#
#    def __init__(self) -> None:
#        super().__init__()
#        self.add_output("Value", data_type=COLOR_PORT)

# class PanTiltNode(RegisteredBaseNode):
#    """Filter to represent a pan/tilt position."""
#    NODE_NAME = "Pan-Tilt Filter"
#    __identifier__ = "constant"
#    __representation__ = -5
