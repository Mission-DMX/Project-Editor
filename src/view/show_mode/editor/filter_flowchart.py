"""Extended Flowchart to handle creating nodes from file"""
from typing import override

from pyqtgraph.flowchart import Flowchart
from pyqtgraph.flowchart.NodeLibrary import NodeLibrary
from PySide6.QtGui import QBrush, QColor

from model import Filter, Scene
from model.scene import FilterPage

from .nodes.base.filternode import FilterNode


class FilterFlowchart(Flowchart):
    """Flowchart that can handle creating nodes from file"""

    def __init__(self, page: FilterPage, terminals: dict[str, dict[str, str]] = None, file_path: str = None,
                 library: NodeLibrary = None) -> None:
        super().__init__(terminals, page.parent_scene.human_readable_name + "/" + page.name, file_path, library)
        self._page = page

    @property
    def show_scene(self) -> Scene:
        """The scene this flowchart represents"""
        return self._page.parent_scene

    @override
    def createNode(self, node_type: int, name: str = None, pos: tuple[int, int] = None) -> FilterNode:
        """Adds a node to the flowchart. Overrides Flowchart behaviour by passing scene to node.

        Args:
            node_type: The type of the node.
            name: The name of the node.
            pos: The position of the node
        """
        if name is None:
            name = node_type
            index = 0
            page_name = (self._page.name + ".") if self._page.name != "default" else ""
            while True:
                tmp = f"{page_name}{name}.{index}"
                if tmp not in self._nodes:
                    name = tmp
                    break
                index += 1
        node: FilterNode = self.library.getNodeType(node_type)(self._page.parent_scene, name)
        self._page.filters.append(node.filter)
        self.addNode(node, name, pos)
        return node

    def create_node_with_filter(self, filter_: Filter, node_type: int,
                                is_from_different_page: bool = False) -> FilterNode:
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

    @override
    def addNode(self, node: FilterNode, name: str, pos: tuple[int, int] = None) -> None:
        """Adds a node to the flowchart.

        Args:
            node: Node to be added.
            name: Name of the node.
            pos: Position of the node.
        """
        if isinstance(node, FilterNode) and pos is not None:
            node.filter.pos = pos
        super().addNode(node, name, pos)
