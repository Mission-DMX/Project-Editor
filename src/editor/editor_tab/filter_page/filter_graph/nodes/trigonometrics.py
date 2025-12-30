"""Trigonometric nodes for the Node Editor."""
from NodeGraphQt import BaseNode, NodeGraph

from editor.editor_tab.filter_page.filter_graph.nodes.ports import DOUBLE_PORT
from editor.editor_tab.filter_page.filter_graph.nodes.registered_base_node import RegisteredBaseNode


def register_trigonometric_nodes(graph: NodeGraph) -> None:
    """
    Register all trigonometric nodes in a node graph.
    Args:
        graph: the node graph to register the nodes in.

    """
    graph.register_node(SinNode)
    graph.register_node(CosNode)
    graph.register_node(TanNode)
    graph.register_node(ArcSinNode)
    graph.register_node(ArcCosNode)
    graph.register_node(ArcTanNode)


class TrigonometricNode(RegisteredBaseNode):
    """Base class for trigonometric nodes."""

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_input("factor_outer", data_type=DOUBLE_PORT)
        self.add_input("factor_inner", data_type=DOUBLE_PORT)
        self.add_input("phase", data_type=DOUBLE_PORT)
        self.add_input("offset", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class SinNode(TrigonometricNode):
    """Filter to calculate sin value.

    value = factor_outer*sin((value_in+phase)*factor_inner) + offset
    """
    NODE_NAME = "Sin"
    __identifier__ = "trigonometric"
    __representation__ = 19


class CosNode(TrigonometricNode):
    """ Filter to calculate cos value.

    value = factor_outer*cos((value_in+phase)*factor_inner) + offset
    """
    NODE_NAME = "Cos"
    __identifier__ = "trigonometric"
    __representation__ = 20


class TanNode(TrigonometricNode):
    """Filter to calculate tan value.

    value = factor_outer*tan((value_in+phase)*factor_inner) + offset
    """
    NODE_NAME = "Tan"
    __identifier__ = "trigonometric"
    __representation__ =21


class ArcSinNode(RegisteredBaseNode):
    """Filter to calculate arcSin value.

    value = arcSin(value_in)
    """
    NODE_NAME = "ArcSin"
    __identifier__ = "trigonometric"
    __representation__ =22

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class ArcCosNode(RegisteredBaseNode):
    """Filter to calculate arcCos value.

    value = arcCos(value_in)
    """
    NODE_NAME = "ArcCos"
    __identifier__ = "trigonometric"
    __representation__ =23

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class ArcTanNode(RegisteredBaseNode):
    """Filter to calculate arcTan value.

    value = arcTan(value_in)
    """
    NODE_NAME = "ArcTan"
    __identifier__ = "trigonometric"
    __representation__ = 24

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)
