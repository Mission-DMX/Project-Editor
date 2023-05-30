# coding=utf-8
"""Basic filter node"""
import logging

from pyqtgraph.flowchart.Flowchart import Node, Terminal
from PySide6.QtGui import QFont

from model import Scene, Filter, DataType, Broadcaster

from ..node_graphics_item import FilterSettingsItem


class FilterNode(Node):
    """Basic filter node."""

    def __init__(self, model: Filter | Scene,
                 filter_type: int,
                 name: str,
                 terminals: dict[str, dict[str, str]] = None):
        super().__init__(name, terminals)
        if isinstance(model, Scene):
            self._filter = Filter(scene=model, filter_id=name, filter_type=filter_type)
        elif isinstance(model, Filter):
            self._filter = model
        else:
            logging.warning("Tried creating filter node with unknown model %s", str(type(model)))
        # Dict with entries (channel, DataType)
        self._in_value_types: dict[str, DataType] = {}
        self._out_value_types: dict[str, DataType] = {}

        # self.fsi = FilterSettingsItem(self, self.graphicsItem())
        self.fsi = FilterSettingsItem(self._filter, self.graphicsItem())
        font: QFont = self.graphicsItem().nameItem.font()
        font.setPixelSize(12)
        self.graphicsItem().nameItem.setFont(font)
        self.graphicsItem().xChanged.connect(self.update_filter_pos)

    def connected(self, localTerm: Terminal, remoteTerm: Terminal):
        """Handles behaviour if terminal was connected. Adds channel link to filter.
        Could emit signals. See pyqtgraph.flowchart.Node.connected()

        Args:
            localTerm: The terminal on the node itself.
            remoteTerm: The terminal of the other node.
        """
        remote_node = remoteTerm.node()

        if not localTerm.isInput() or not remoteTerm.isOutput():
            return

        if not isinstance(remote_node, FilterNode):
            logging.warning("Tried to non-FilterNode nodes. Forced disconnection.")
            localTerm.disconnectFrom(remoteTerm)
            return

        if not self._in_value_types[localTerm.name()] == remote_node.out_value_types[remoteTerm.name()]:
            logging.warning("Tried to connect incompatible filter channels. Forced disconnection.")
            localTerm.disconnectFrom(remoteTerm)
            return

        self.filter.channel_links[localTerm.name()] = remote_node.name() + ":" + remoteTerm.name()

    def disconnected(self, localTerm, remoteTerm):
        """Handles behaviour if terminal was disconnected. Removes channel link from filter.
        Could emit signals. See pyqtgraph.flowchart.Node.disconnected()

        Args:
            localTerm: The terminal on the node itself.
            remoteTerm: The terminal of the other node.
        """
        if localTerm.isInput() and remoteTerm.isOutput():
            self.filter.channel_links[localTerm.name()] = ""

    def rename(self, name):
        """Handles behaviour if node was renamed. Changes filter.id.
        Could emit signals. See pyqtgraph.flowchart.Node.rename()

        Args:
            name: The new name of the filter.

        Returns:
            The return value of pyqtgraph.flowchart.Node.rename()
        """
        self.filter.filter_id = name
        return super().rename(name)

    def update_filter_pos(self):
        """Saves nodes position inside the ui to registered filter."""
        pos = self.graphicsItem().pos()
        self._filter.pos = (pos.x(), pos.y())

    @property
    def filter(self) -> Filter:
        """The corresponding filter"""
        return self._filter

    @property
    def in_value_types(self) -> dict[str, DataType]:
        """Dict mapping the names to the data types of the input channels."""
        return self._in_value_types

    @property
    def out_value_types(self) -> dict[str, DataType]:
        """Dict mapping the names to the data types of the output channels."""
        return self._out_value_types
