"""All nodes used for debugging purposes."""
from NodeGraphQt import NodeGraph

from editor.editor_tab.filter_page.filter_graph.nodes.ports import BIT_16_PORT, BIT_8_PORT, COLOR_PORT, DOUBLE_PORT
from editor.editor_tab.filter_page.filter_graph.nodes.registered_base_node import RegisteredBaseNode


def register_debug_nodes(graph: NodeGraph) -> None:
    """
    Register all constant nodes in a node graph.
    Args:
        graph: the node graph to register the nodes in.
    """
    graph.register_node(Bit8Node)
    graph.register_node(Bit16Node)
    graph.register_node(FloatNode)
    graph.register_node(ColorNode)
    graph.register_node(RemoteBit8Node)
    graph.register_node(RemoteBit16Node)
    graph.register_node(RemoteFloatNode)
    graph.register_node(RemoteColorNode)


class Bit8Node(RegisteredBaseNode):
    """Filter to debug an 8-bit value.
    TODO implement visualization
    """
    NODE_NAME = "8-Bit Filter"
    __identifier__ = "debug"
    __representation__ = 4

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_8_PORT)


class Bit16Node(RegisteredBaseNode):
    """Filter to debug an 16-bit value.
    TODO implement visualization
    """
    NODE_NAME = "16-Bit Filter"
    __identifier__ = "debug"
    __representation__ = 5

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_16_PORT)


class FloatNode(RegisteredBaseNode):
    """Filter to debug an Float value.
    TODO implement visualization
    """
    NODE_NAME = "Float Filter"
    __identifier__ = "debug"
    __representation__ = 6

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=DOUBLE_PORT)


class ColorNode(RegisteredBaseNode):
    """Filter to debug an Color value.
    TODO implement visualization"""
    NODE_NAME = "Float Filter"
    __identifier__ = "debug"
    __representation__ = 7

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=COLOR_PORT)


class RemoteBit8Node(RegisteredBaseNode):
    """Filter to debug an 8-bit value Remote.
    TODO implement visualization
    """
    NODE_NAME = "Remote 8-Bit Filter"
    __identifier__ = "debug"
    __representation__ = 65

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_8_PORT)


class RemoteBit16Node(RegisteredBaseNode):
    """Filter to debug an 16-bit value remote.
    TODO implement visualization
    """
    NODE_NAME = "Remote 16-Bit Filter"
    __identifier__ = "debug"
    __representation__ = 66

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=BIT_16_PORT)


class RemoteFloatNode(RegisteredBaseNode):
    """Filter to debug an Float value remote.
    TODO implement visualization
    """
    NODE_NAME = "Remote Float Filter"
    __identifier__ = "debug"
    __representation__ = 67

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=DOUBLE_PORT)


class RemoteColorNode(RegisteredBaseNode):
    """Filter to debug an Color value remote.
    TODO implement visualization"""
    NODE_NAME = "Float Filter"
    __identifier__ = "debug"
    __representation__ = 68

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Value", data_type=COLOR_PORT)
