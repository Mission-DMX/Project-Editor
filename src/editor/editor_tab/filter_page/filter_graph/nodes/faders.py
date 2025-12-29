"""Fader nodes for the Node Editor."""
from NodeGraphQt import BaseNode, NodeGraph

from editor.editor_tab.filter_page.filter_graph.nodes.ports import BIT_16_PORT, BIT_8_PORT, DOUBLE_PORT


def register_fader_nodes(graph: NodeGraph) -> None:
    """
    Register all fader nodes in a node graph.
    Args:
        graph: the node graph to register the nodes in.

    """
    #TODO: