"""Module containing node editor"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING

from NodeGraphQt import BaseNode, NodeGraph
from PySide6.QtWidgets import QWidget

from editor.editor_tab.filter_page.filter_graph.nodes.adapters import register_adapter_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.arithmetics import register_arithmetic_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.color_manipulation import register_color_manipulation_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.constants import register_constant_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.debug import register_debug_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.effects import register_effect_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.faders import register_fader_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.fixture import FixtureNode
from editor.editor_tab.filter_page.filter_graph.nodes.scripts import register_script_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.sub import SubNode
from editor.editor_tab.filter_page.filter_graph.nodes.times import register_time_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.trigonometrics import register_trigonometric_nodes
from editor.editor_tab.filter_page.filter_graph.nodes.waves import register_wave_nodes

if TYPE_CHECKING:
    from model.filter import Filter,Scene

logger = getLogger(__name__)


def toggle_node_search(graph):
    """
    show/hide the node search widget.
    """
    graph.toggle_node_search()


class FilterGraphWidget(NodeGraph):
    """Nodeeditor to edit scenes and their filter nodes"""

    def __init__(self, parent_scene: Scene, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._parent_scene = parent_scene
        self._name = ""
        self._register_all_nodes()
        self.property_changed.connect(self._property_changed)

        self.set_context_menu_from_file(str(Path(Path(__file__).parent.resolve(), 'context_menu', 'context_menu.json')),
                                        'graph')

    @property
    def name(self) -> str:
        """Name."""
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = str(new_name)

    @property
    def parent_scene(self) -> Scene:
        """Parent scene."""
        return self._parent_scene

    @property  # TODO
    def filters(self) -> list[Filter]:
        return []

    # @property TODO
    # def filters(self) -> list[BaseNode]:
    #    return self.all_nodes()

    def _register_all_nodes(self):
        """Register nodes in the flowchart."""
        register_constant_nodes(self)
        register_debug_nodes(self)
        register_adapter_nodes(self)
        register_arithmetic_nodes(self)
        register_trigonometric_nodes(self)
        register_wave_nodes(self)
        register_time_nodes(self)
        register_effect_nodes(self)
        register_fader_nodes(self)
        register_script_nodes(self)
        register_color_manipulation_nodes(self)
        self.register_node(FixtureNode)
        self.register_node(SubNode)

    def _property_changed(self, node: BaseNode, prop_name: str, prop_value: str) -> None:
        if prop_name == "name" and isinstance(node, FixtureNode):
            node.name_change(prop_value)
