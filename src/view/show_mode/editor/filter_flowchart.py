# encoding=utf-8
"""Extended Flowchart to handle creating nodes from file"""
from PySide6.QtGui import QBrush, QColor
from pyqtgraph.flowchart import Flowchart

from model import Filter, Scene
from model.scene import FilterPage
from .nodes.base.filternode import FilterNode


class FilterFlowchart(Flowchart):
    """Flowchart that can handle creating nodes from file"""

    def __init__(self, page: FilterPage, terminals=None, filePath=None, library=None):
        super().__init__(terminals, page.parent_scene.human_readable_name + "/" + page.name, filePath, library)
        self._page = page

    @property
    def show_scene(self) -> Scene:
        """The scene this flowchart represents"""
        return self._page.parent_scene

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
                tmp = f"{name}.{index}"
                if tmp not in self._nodes:
                    name = tmp
                    break
                index += 1
        node: FilterNode = self.library.getNodeType(nodeType)(self._page.parent_scene, name)
        self._page.filters.append(node.filter)
        self.addNode(node, name, pos)
        return node

    def create_node_with_filter(self, filter_: Filter, node_type, is_from_different_page: bool = False):
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
        node: FilterNode = self.library.getNodeType(node_type)(filter_, filter_.filter_id)
        if is_from_different_page:
            b: QBrush = node.graphicsItem().brush
            b.setColor(QColor.fromRgb(30, 40, 30, 255))
            node.graphicsItem().setBrush(b)
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
