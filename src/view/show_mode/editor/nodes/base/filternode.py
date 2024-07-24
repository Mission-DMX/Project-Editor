# coding=utf-8
"""Basic filter node"""
from logging import getLogger

from pyqtgraph.flowchart.Flowchart import Node, Terminal
from PySide6.QtGui import QFont


from model import Scene, Filter
from model.virtual_filters.vfilter_factory import construct_virtual_filter_instance

from src.view.show_mode.editor.filter_settings_item import FilterSettingsItem
from view.show_mode.editor.nodes.base.filternode_graphicsitem import FilterNodeGraphicsItem

logger = getLogger(__name__)


class FilterNode(Node):
    """Basic filter node."""

    def __init__(self, model: Filter | Scene,
                 filter_type: int,
                 name: str,
                 terminals: dict[str, dict[str, str]] = None,
                 allowAddInput: bool = False,
                 allowAddOutput: bool = False):
        if isinstance(model, Scene):
            if filter_type < 0:
                self._filter = construct_virtual_filter_instance(scene=model, filter_id=name, filter_type=filter_type)
            else:
                self._filter = Filter(scene=model, filter_id=name, filter_type=filter_type)
            model.append_filter(self._filter)
        elif isinstance(model, Filter):
            self._filter = model
        else:
            self._filter = None
            logger.warning("Tried creating filter node with unknown model %s", str(type(model)))

        super().__init__(name, terminals, allowAddInput=allowAddInput, allowAddOutput=allowAddOutput)

        self.fsi = FilterSettingsItem(self, self.graphicsItem())
        font: QFont = self.graphicsItem().nameItem.font()
        font.setPixelSize(12)
        self.graphicsItem().nameItem.setFont(font)
        self.graphicsItem().xChanged.connect(self.update_filter_pos)
        self.channel_hints = {}

    def graphicsItem(self):
        """Return the GraphicsItem for this node. Subclasses may re-implement
        this method to customize their appearance in the flowchart."""
        if self._graphicsItem is None:
            self._graphicsItem = FilterNodeGraphicsItem(self)
        return self._graphicsItem

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
            logger.warning("Tried to non-FilterNode nodes. Forced disconnection. Got type: " + str(type(remote_node)) +
                           " and expected: " + str(FilterNode.__class__) + " instance.")
            localTerm.disconnectFrom(remoteTerm)
            return

        try:
            if not self.filter.in_data_types[localTerm.name()] == remote_node.filter.out_data_types[remoteTerm.name()]:
                logger.warning("Tried to connect incompatible filter channels. Forced disconnection.")
                localTerm.disconnectFrom(remoteTerm)
                return
            self.filter.channel_links[localTerm.name()] = remote_node.name() + ":" + remoteTerm.name()
        except KeyError as e:
            logger.error(str(e) + " Possible key candidates are: " + ", ".join(self.filter.in_data_types.keys()) +
                         "\nRemote options are: " + ", ".join(remote_node.filter.out_data_types.keys()))

    def disconnected(self, localTerm, remoteTerm):
        """Handles behaviour if terminal was disconnected. Removes channel link from filter.
        Could emit signals. See pyqtgraph.flowchart.Node.disconnected()

        Args:
            localTerm: The terminal on the node itself.
            remoteTerm: The terminal of the other node.
        """
        if localTerm.isInput() and remoteTerm.isOutput():
            self.filter.channel_links[localTerm.name()] = ""

    def rename(self, name: str):
        """Handles behaviour if node was renamed. Changes filter.id.
        Could emit signals. See pyqtgraph.flowchart.Node.rename()

        Args:
            name: The new name of the filter.

        Returns:
            The return value of pyqtgraph.flowchart.Node.rename()
        """
        name = name.replace(":", "_")
        # check for name collision
        name = self.filter.scene.ensure_name_uniqueness(name)

        old_name = self.filter.filter_id
        self.filter.filter_id = name
        filters_to_update: set[Filter] = set()
        for terminal in self.outputs().values():
            for next_filter_node in terminal.dependentNodes():
                if isinstance(next_filter_node, FilterNode):
                    filters_to_update.add(next_filter_node.filter)
        for filter in filters_to_update:
            for input_key in filter.channel_links.keys():
                # FIXME the name is not always present
                prefix, suffix = filter.channel_links[input_key].split(":")
                if prefix == old_name:
                    filter.channel_links[input_key] = "{}:{}".format(name, suffix)
        return super().rename(name)

    def update_filter_pos(self):
        """Saves nodes position inside the ui to registered filter."""
        pos = self.graphicsItem().pos()
        self._filter.pos = (pos.x(), pos.y())

    @property
    def filter(self) -> Filter:
        """The corresponding filter"""
        return self._filter

    def update_node_after_settings_changed(self):
        """Override this method in order to update ports after the settings have changed"""
        pass

    def close(self):
        """Closes the node and removes the linked filter from the scene."""
        self.filter.scene.remove_filter(self.filter)
        super().close()
