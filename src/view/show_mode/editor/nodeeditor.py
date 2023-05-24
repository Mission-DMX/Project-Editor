# coding=utf-8
"""Module containing node editor"""
import logging

from PySide6.QtWidgets import QWidget, QDialog, QGridLayout
from pyqtgraph.flowchart.Flowchart import Flowchart, Terminal

from model import Scene, Filter
from . import nodes
from .nodes import FilterNode


class NodeEditorDialog(QDialog):
    """Nodeeditor to edit scenes and their filter nodes"""
    
    def __init__(self, scene: Scene) -> None:
        super().__init__()
        self._scene = scene

        # Flag to differentiate between loading filters from file and creating filters.
        self._loading = False

        self._scene.flowchart.removeNode(self._scene.flowchart.outputNode)
        self._scene.flowchart.removeNode(self._scene.flowchart.inputNode)

        self._scene.flowchart.sigChartChanged.connect(self._set_filter_on_node)

        self.setLayout(QGridLayout())
        self.layout().addWidget(self._scene.flowchart.widget().chartWidget.viewDock)

        self.add_filters(self._scene.filters)

    def _set_filter_on_node(self, _, action, node):
        if not isinstance(node, FilterNode):
            logging.warning("Tried to add an unknown node: %s", node)
            return
            # raise TypeError("Node type not known")
        if action == 'remove':
            try:
                self._scene.filters.remove(node.filter)
                logging.debug("Removed filter %s", node.filter.filter_id)
            except ValueError:
                logging.warning("Filter of removed node was not registered")

        elif action == 'add':
            if self._loading:
                for filter_ in self._scene.filters:
                    if filter_.filter_id == node.name():
                        node.setup_filter(filter_)
                        node.graphicsItem().setPos(filter_.pos[0], filter_.pos[1])
                        logging.debug("Added and set up filter %s", filter_.filter_id)

            elif node.filter not in self._scene.filters:
                node.update_filter_pos()
                self._scene.filters.append(node.filter)
                if node.filter.filter_type == 11:
                    node.filter.board_configuration = self._scene.board_configuration

    def add_filter(self, filter_: Filter):
        """Add a single filter from outside the nodeeditor.
        
        Args:
            filter_: The filter for which a node should be created.
        """
        self._scene.flowchart.createNode(nodes.type_to_node[filter_.filter_type], name=filter_.filter_id)

    def add_filters(self, filters: list[Filter]):
        """Handle loading an entire scene.
        
        Args:
            filters: The filters of the scene to be added.
        """
        # Set flag for _set_filter_on_node()
        self._loading = True
        for filter_ in filters:
            self.add_filter(filter_)
        self._loading = False

        # Create connections inside nodeeditor
        for name, node in self._scene.flowchart.nodes().items():
            if not isinstance(node, FilterNode):
                logging.warning("Trying to connect non-FilterNode %s", name)
                continue

            for input_channel, output_channel in node.filter.channel_links.items():
                if output_channel == "":
                    continue
                remote_name = output_channel.split(':')[0]
                remote_term = output_channel.split(':')[1]
                remote_node = self._scene.flowchart.nodes()[remote_name]
                if not isinstance(remote_node, FilterNode):
                    logging.warning("Trying to connect node %s to non-FilterNode %s", name, remote_name)
                remote_term = remote_node.outputs()[remote_term]
                local_term = node.inputs()[input_channel]
                if not isinstance(remote_term, Terminal) or not isinstance(local_term, Terminal):
                    logging.critical("Fetched non-terminal object while trying to connect terminals")
                    continue
                self._scene.flowchart.connectTerminals(local_term, remote_term)

    @property
    def scene(self) -> Scene:
        """The scene of the tab"""
        return self._scene

    @property
    def flowchart(self) -> Flowchart:
        """The flowchart of the scene"""
        return self._scene.flowchart