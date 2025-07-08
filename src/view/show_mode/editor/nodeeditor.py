"""Module containing node editor"""
from logging import getLogger

from pyqtgraph.flowchart.Flowchart import Flowchart, Terminal
from PySide6.QtWidgets import QGridLayout, QWidget

from model import Scene
from model.scene import FilterPage
from view.show_mode.editor.nodes.filter_node_library import FilterNodeLibrary

from .filter_flowchart import FilterFlowchart
from .nodes.base.filternode import FilterNode
from .nodes.type_to_node_dict import type_to_node

logger = getLogger(__name__)


class NodeEditorWidget(QWidget):
    """Nodeeditor to edit scenes and their filter nodes"""

    def __init__(self, page_or_scene: Scene | FilterPage, parent: QWidget) -> None:
        super().__init__(parent)
        if isinstance(page_or_scene, Scene):
            self._page: FilterPage = page_or_scene.pages[0]
        else:
            self._page = page_or_scene

        # Flag to differentiate between loading filters from file and creating filters.
        self._loading = False
        self._library = FilterNodeLibrary()

        layout = QGridLayout()
        self.setLayout(layout)

        self._populate_flowchart()

    def _populate_flowchart(self):
        self._flowchart = FilterFlowchart(page=self._page, library=self._library)
        self._flowchart.removeNode(self._flowchart.outputNode)
        self._flowchart.removeNode(self._flowchart.inputNode)
        loaded_in_filters: set[str] = set()
        required_filters: set[str] = set()
        for filter_ in self._page.filters:
            self._flowchart.create_node_with_filter(filter_=filter_, node_type=type_to_node[filter_.filter_type])
            loaded_in_filters.add(filter_.filter_id)
            for remote_filter_channel in filter_.channel_links.values():
                if not remote_filter_channel:
                    continue
                filter_name, _ = remote_filter_channel.split(":")
                required_filters.add(filter_name)
        still_missing_filters = required_filters - loaded_in_filters
        for filter_candidate in self._page.parent_scene.filters:
            if len(still_missing_filters) < 1:
                break
            if filter_candidate.filter_id in still_missing_filters:
                still_missing_filters.remove(filter_candidate.filter_id)
                logger.info("Adding foreign filter '%s' from scene '%s'.", filter_candidate.filter_id,
                            self._page.parent_scene)
                self._flowchart.create_node_with_filter(
                    filter_=filter_candidate,
                    node_type=type_to_node[filter_candidate.filter_type], is_from_different_page=True
                )
        if len(still_missing_filters) > 0:
            raise Exception(f"Missing filters '{still_missing_filters}' in scene '{self._page.parent_scene}'.")
        for name, node in self._flowchart.nodes().items():
            if not isinstance(node, FilterNode):
                logger.warning("Trying to connect non-FilterNode %s. Got type: %s. Expected: %s",
                               name, str(type(node)), str(FilterNode.__class__))
                continue
            for input_channel, output_channel in node.filter.channel_links.items():
                if not isinstance(output_channel, str) or len(output_channel) == 0:
                    continue
                remote_name = output_channel.split(":")[0]
                remote_term = output_channel.split(":")[1]
                fc_nodes = self._flowchart.nodes()
                remote_node = fc_nodes.get(remote_name)
                if remote_node is None:
                    logger.error("%s not in flowchart nodes. Is it an external one? Skipping.", remote_name)
                    continue
                if not isinstance(remote_node, FilterNode):
                    logger.warning("Trying to connect node %s to non-FilterNode %s", name, remote_name)
                remote_term = remote_node.outputs().get(remote_term)
                local_term = node.inputs().get(input_channel)
                if not isinstance(remote_term, Terminal) or not isinstance(local_term, Terminal):
                    logger.critical("Fetched non-terminal object while trying to "
                                    "connect terminals %s -> %s", remote_term, local_term)
                    continue
                self._flowchart.connectTerminals(local_term, remote_term)
        self.layout().addWidget(self._flowchart.widget().chartWidget.viewDock)

    @property
    def scene(self) -> Scene:
        """The scene of the tab"""
        return self._page.parent_scene

    @property
    def flowchart(self) -> Flowchart:
        """The flowchart of the scene"""
        return self._flowchart

    def refresh(self):
        self.layout().removeWidget(self._flowchart.widget().chartWidget.viewDock)
        self._populate_flowchart()
