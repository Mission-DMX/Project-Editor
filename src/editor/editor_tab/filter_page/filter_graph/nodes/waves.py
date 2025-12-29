"""Wave nodes for the Node Editor."""
from NodeGraphQt import NodeGraph

from editor.editor_tab.filter_page.filter_graph.nodes.ports import DOUBLE_PORT
from editor.editor_tab.filter_page.filter_graph.nodes.trigonometrics import TrigonometricNode


def register_wave_nodes(graph: NodeGraph) -> None:
    """
    Register all constant nodes in a node graph.
    Args:
        graph: the node graph to register the nodes in.

    """
    graph.register_node(SquareWaveNode)
    graph.register_node(TriangleWaveNode)
    graph.register_node(SawtoothWaveNode)


class SquareWaveNode(TrigonometricNode):
    """Filter to generate a square wave."""
    NODE_NAME = "Square Wave"
    __identifier__ = "wave"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("Frequency", data_type=DOUBLE_PORT)


class TriangleWaveNode(TrigonometricNode):
    """Filter to generate a triangle wave."""
    NODE_NAME = "Triangle Wave"
    __identifier__ = "wave"


class SawtoothWaveNode(TrigonometricNode):
    """Filter to generate a sawtooth wave."""
    NODE_NAME = "Sawtooth Wave"
    __identifier__ = "wave"
