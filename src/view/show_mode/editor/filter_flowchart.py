# encoding=utf-8
"""Extended Flowchart to handle creating nodes from file"""
from pyqtgraph.flowchart import Flowchart

from model import Scene, Filter
from .nodes import FilterNode


class FilterFlowchart(Flowchart):
    """Flowchart that can handle creating nodes from file"""
    def __init__(self, scene: Scene, terminals=None, filePath=None, library=None):
        super().__init__(terminals, scene.human_readable_name, filePath, library)
        self._scene = scene

    @property
    def show_scene(self):
        """The scene this flowchart represents"""
        return self._scene

    def createNode(self, nodeType, name=None, pos=None):
        """Adds a node to the flowchart. Overrides Flowchart behaviour by passing scene to node.

        Args:
            nodeType: The type of the node.
            name: The name of the node.
            pos: The position of the node
        """
        if name is None:
            name = nodeType
            index = 0
            while True:
                name = f"{name}.{index}"
                if name not in self._nodes:
                    break
                index += 1

        node = self.library.getNodeType(nodeType)(self._scene, name)
        self.addNode(node, name, pos)
        return node

    def create_node_with_filter(self, filter_: Filter, node_type):
        """Creates a node and adds it to the flowchart.

        Args:
            filter_: The filter of the filter node.
            node_type: The type of the node.
        """
        if filter_.filter_id in self._nodes:
            index = 0
            while True:
                name = f"{filter_.filter_id}.{index}"
                if name not in self._nodes:
                    filter_.filter_id = name
                    break
                index += 1
        node = self.library.getNodeType(node_type)(filter_, filter_.filter_id)
        self.addNode(node, filter_.filter_id, filter_.pos)
        return node

    def addNode(self, node, name, pos=None):
        """Adds a node to the flowchart.

        Args:
            node: Node to be added.
            name: Name of the node.
            pos: Position of the node.
        """
        if isinstance(node, FilterNode) and pos is not None:
            node.filter.pos = pos
        return super().addNode(node, name, pos)
