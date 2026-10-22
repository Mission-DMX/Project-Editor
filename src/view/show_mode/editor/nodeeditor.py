"""Module containing node editor"""
from logging import getLogger
from typing import override

from pyqtgraph.flowchart.Flowchart import Flowchart, Terminal
from pyqtgraph.flowchart.Terminal import ConnectionItem
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QGridLayout, QWidget

from model import Scene
from model.broadcaster import Broadcaster
from model.filter import VirtualFilter
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
        self._pick_mode_active: bool = False

        layout = QGridLayout()
        self.setLayout(layout)

        self._populate_flowchart()

        broadcaster = Broadcaster()
        broadcaster.scope_edge_pick_requested.connect(self._enter_pick_mode)
        broadcaster.scope_edge_pick_cancelled.connect(self._exit_pick_mode)

    def _populate_flowchart(self) -> None:
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
                    node_type=type_to_node[filter_candidate.filter_type], is_from_different_page=True,
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

    def refresh(self) -> None:
        self.layout().removeWidget(self._flowchart.widget().chartWidget.viewDock)
        self._populate_flowchart()

    def _enter_pick_mode(self) -> None:
        # Only the visible editor should capture the next edge click.
        if not self.isVisible() or self._pick_mode_active:
            return
        self._pick_mode_active = True
        scene = self._flowchart.scene
        if scene is not None:
            scene.installEventFilter(self)
        view = self._flowchart.widget().chartWidget.view
        view.setCursor(Qt.CursorShape.CrossCursor)

    def _exit_pick_mode(self) -> None:
        if not self._pick_mode_active:
            return
        self._pick_mode_active = False
        scene = self._flowchart.scene
        if scene is not None:
            scene.removeEventFilter(self)
        view = self._flowchart.widget().chartWidget.view
        view.unsetCursor()

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not self._pick_mode_active:
            return super().eventFilter(watched, event)
        if event.type() == QEvent.Type.GraphicsSceneMousePress and isinstance(event, QGraphicsSceneMouseEvent):
            if event.button() == Qt.MouseButton.RightButton:
                Broadcaster().scope_edge_pick_cancelled.emit()
                return True
            if event.button() != Qt.MouseButton.LeftButton:
                return super().eventFilter(watched, event)
            scene = self._flowchart.scene
            if scene is None:
                return super().eventFilter(watched, event)
            for item in scene.items(event.scenePos()):
                if isinstance(item, ConnectionItem):
                    # pyqtgraph's source/target orientation depends on which
                    # end initiated the connection drag, so pick whichever is
                    # the output terminal.
                    endpoints = [item.source.term, item.target.term]
                    output_terms = [t for t in endpoints if t.isOutput()]
                    if not output_terms:
                        continue
                    out_term: Terminal = output_terms[0]
                    source_filter_node = out_term.node()
                    source_filter = getattr(source_filter_node, "filter", None)
                    port_name = out_term.name()
                    if isinstance(source_filter, VirtualFilter):
                        resolved = source_filter.resolve_output_port_id(port_name)
                        if resolved is None:
                            logger.warning("Virtual filter %s has no output port %s",
                                           source_filter.filter_id, port_name)
                            Broadcaster().scope_edge_pick_cancelled.emit()
                            return True
                        channel_id = resolved
                    else:
                        channel_id = f"{source_filter_node.name()}:{port_name}"
                    data_type = source_filter.out_data_types.get(port_name) if source_filter else None
                    Broadcaster().scope_edge_picked.emit(channel_id, data_type)
                    Broadcaster().scope_edge_pick_cancelled.emit()
                    return True
            # Click missed a connection — cancel so the user isn't stuck.
            Broadcaster().scope_edge_pick_cancelled.emit()
            return True
        return super().eventFilter(watched, event)
