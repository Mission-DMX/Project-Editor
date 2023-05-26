# coding=utf-8
"""Module containing node editor"""
import logging

from PySide6.QtWidgets import QDialog, QGridLayout
from pyqtgraph.flowchart.Flowchart import Flowchart, Terminal

# from model import Scene, Filter
from model import Scene
from . import nodes
from .flowchart import FilterFlowchart
from .nodes import FilterNode
from .filter_node_library import FilterNodeLibrary


class NodeEditorDialog(QDialog):
    """Nodeeditor to edit scenes and their filter nodes"""

    def __init__(self, scene: Scene) -> None:
        super().__init__()
        self._scene = scene

        # Flag to differentiate between loading filters from file and creating filters.
        self._loading = False

        self._flowchart = FilterFlowchart(scene=self._scene, library=FilterNodeLibrary())

        self._flowchart.removeNode(self._flowchart.outputNode)
        self._flowchart.removeNode(self._flowchart.inputNode)

        self.setLayout(QGridLayout())
        self.layout().addWidget(self._flowchart.widget().chartWidget.viewDock)

        for filter_ in self._scene.filters:
            self._flowchart.create_node_with_filter(filter_=filter_, node_type=nodes.type_to_node[filter_.filter_type])

        for name, node in self._flowchart.nodes().items():
            if not isinstance(node, FilterNode):
                logging.warning("Trying to connect non-FilterNode %s", name)
                continue
            for input_channel, output_channel in node.filter.channel_links.items():
                if output_channel == "":
                    continue
                remote_name = output_channel.split(':')[0]
                remote_term = output_channel.split(':')[1]
                remote_node = self._flowchart.nodes()[remote_name]
                if not isinstance(remote_node, FilterNode):
                    logging.warning("Trying to connect node %s to non-FilterNode %s", name, remote_name)
                remote_term = remote_node.outputs()[remote_term]
                local_term = node.inputs()[input_channel]
                if not isinstance(remote_term, Terminal) or not isinstance(local_term, Terminal):
                    logging.critical("Fetched non-terminal object while trying to connect terminals")
                    continue
                self._flowchart.connectTerminals(local_term, remote_term)

    @property
    def scene(self) -> Scene:
        """The scene of the tab"""
        return self._scene

    @property
    def flowchart(self) -> Flowchart:
        """The flowchart of the scene"""
        return self._flowchart
