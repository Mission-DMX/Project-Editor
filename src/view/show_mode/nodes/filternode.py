# coding=utf-8
"""Basic filter node"""
import logging

from pyqtgraph.flowchart.Flowchart import Node, Terminal
from PySide6.QtGui import QFont

from model import DataType, Filter

from ..node_graphics_item import FilterSettingsItem


class FilterNode(Node):
    """Basic filter node."""

    def __init__(self, filter_type: int, name: str, terminals: dict[str, dict[str, str]] = None, allow_add_input=False):
        super().__init__(name, terminals, allow_add_input)
        self._filter = Filter(scene=None, filter_id=name, filter_type=filter_type)
        # Dict with entries (channel, DataType)
        self._in_value_types: dict[str, DataType] = {}
        self._out_value_types: dict[str, DataType] = {}

        # Handle special case of universe filter

        self.update_filter_pos()
        self.setup_filter()

    def setup_filter(self, filter_: Filter = None):
        """Sets the filter. Overrides existing filters.

        FilterNode.filter will be set to filter.
        FilterNode.filter.channel_links will be reset.
        """
        # Need to be separate from __init__ to handle creation during loading from file.
        # When loading from file, first the node is created.
        # This triggers a signal inside pyqtgraph which is monitored in SceneTabWidget.
        # When signal is triggered, setup_filter() is called.
        # setup_filter() only gets passed a filter during loading from file.
        # When created through nodeeditor, no filter is passed.
        if filter_ is not None:
            if filter_.filter_type != self._filter.filter_type:
                logging.critical(
                    "Tried to override a filter with a filter of different type (%s vs %s)",
                    filter_.filter_type, self._filter.filter_type)
                return
                # raise ValueError("Filter type wrong")
            self._filter = filter_
        else:
            for key, _ in self.inputs().items():
                self.filter.channel_links[key] = ""

        #if len(self._filter.filter_configurations) > 0 or len(self._filter.initial_parameters) > 0:
        self.fsi = FilterSettingsItem(self._filter, self.graphicsItem())
        font: QFont = self.graphicsItem().nameItem.font()
        font.setPixelSize(12)
        self.graphicsItem().nameItem.setFont(font)
        self.graphicsItem().xChanged.connect(self.update_filter_pos)

        logging.debug("Added filter<type=%s}, id=%s>",
                      self._filter.filter_type, self._filter.filter_id)

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
