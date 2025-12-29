"""Constant nodes for the Node Editor."""
from NodeGraphQt import BaseNode, NodeGraph

from editor.editor_tab.filter_page.filter_graph.nodes.ports import BIT_16_PORT, BIT_8_PORT, DOUBLE_PORT


def register_constant_nodes(graph: NodeGraph) -> None:
    """
    Register all constant nodes in a node graph.
    Args:
        graph: the node graph to register the nodes in.

    """
    graph.register_node(Bit8Node)
    graph.register_node(Bit16Node)
    graph.register_node(FloatNode)


class Bit8Node(BaseNode):
    """Filter to represent an 8-bit value."""
    NODE_NAME = "8-Bit Filter"
    __identifier__ = "constant"

    def __init__(self) -> None:
        super().__init__()
        self.add_output("Value", data_type=BIT_8_PORT)
        self.add_spinbox("value", "value", 0, 0, 255)


class Bit16Node(BaseNode):
    """Filter to represent a 16-bit value."""
    NODE_NAME = "16-Bit Filter"
    __identifier__ = "constant"

    def __init__(self) -> None:
        super().__init__()
        self.add_output("Value", data_type=BIT_16_PORT)
        self.add_spinbox("value", "value", 0, 0, 65535)


class FloatNode(BaseNode):
    """Filter to represent a float/double value."""
    NODE_NAME = "Float Filter"
    __identifier__ = "constant"

    def __init__(self) -> None:
        super().__init__()
        self.add_output("Value", data_type=DOUBLE_PORT)
        self.add_spinbox("value", "value", 0.0, double=True)

# class ColorNode(BaseNode):
#    """Filter to represent a color value.
#    TODO specify color format
#    """
#    NODE_NAME = "Float Filter"
#    __identifier__ = "constant"
#
#    def __init__(self) -> None:
#        super().__init__()
#        self.add_output("Value", data_type=COLOR_PORT)

# class PanTiltNode(BaseNode):
#    """Filter to represent a pan/tilt position."""
#    NODE_NAME = "Pan-Tilt Filter"
#    __identifier__ = "constant"
