"""Basic filter node."""
from logging import getLogger
from typing import TYPE_CHECKING, override

from pyqtgraph.flowchart.Flowchart import Node, Terminal

from model import Filter, Scene
from model.filters.factory import construct_filter_instance
from view.show_mode.editor.filter_settings_item import FilterSettingsItem
from view.show_mode.editor.nodes.base.filternode_graphicsitem import FilterNodeGraphicsItem

if TYPE_CHECKING:
    from PySide6.QtGui import QFont

logger = getLogger(__name__)


class FilterNode(Node):
    """Basic filter node."""

    def __init__(self, model: Filter | Scene,
                 filter_type: int,
                 name: str,
                 terminals: dict[str, dict[str, str]] | None = None,
                 allow_add_input: bool = False,
                 allow_add_output: bool = False) -> None:
        """Initialize filter node."""
        if isinstance(model, Scene):
            self._filter = construct_filter_instance(scene=model, filter_id=name, filter_type=filter_type)
            if self._filter is not None:
                model.append_filter(self._filter)
        elif isinstance(model, Filter):
            self._filter = model
        else:
            self._filter = None
            logger.warning("Tried creating filter node with unknown model %s", str(type(model)))

        if terminals is None and self._filter is not None:
            terminals = self._terminals_from_filter(self._filter)

        super().__init__(name, terminals, allowAddInput=allow_add_input, allowAddOutput=allow_add_output)

        self.fsi = FilterSettingsItem(self, self.graphicsItem(),
                                      self._filter) if self._filter.configuration_supported else None
        font: QFont = self.graphicsItem().nameItem.font()
        font.setPixelSize(12)
        self.graphicsItem().nameItem.setFont(font)
        self.graphicsItem().xChanged.connect(self.update_filter_pos)
        self.channel_hints = {}

    @override
    def graphicsItem(self) -> FilterNodeGraphicsItem:
        """Return the GraphicsItem for this node.

        Subclasses may re-implement this method to customize their appearance in the flowchart.
        """
        if self._graphicsItem is None:
            self._graphicsItem = FilterNodeGraphicsItem(self)
        return self._graphicsItem

    def connected(self, local_term: Terminal, remote_term: Terminal) -> None:
        """Handle behaviour if terminal was connected. Adds channel link to filter.

        Could emit signals. See pyqtgraph.flowchart.Node.connected().

        Args:
            local_term: The terminal on the node itself.
            remote_term: The terminal of the other node.

        """
        remote_node = remote_term.node()

        if not local_term.isInput() or not remote_term.isOutput():
            return

        if not isinstance(remote_node, FilterNode):
            logger.warning(
                "Tried to non-FilterNode nodes. Forced disconnection. Got type: %s and expected: %s instance.",
                str(type(remote_node)), str(FilterNode.__class__))
            local_term.disconnectFrom(remote_term)
            return

        try:
            if self.filter.in_data_types[local_term.name()] != remote_node.filter.out_data_types[remote_term.name()]:
                logger.warning("Tried to connect incompatible filter channels. Forced disconnection.")
                local_term.disconnectFrom(remote_term)
                return
            self.filter.channel_links[local_term.name()] = remote_node.name() + ":" + remote_term.name()
        except KeyError as e:
            logger.exception("%s Possible key candidates are: %s\nRemote options are: %s", str(e),
                             ", ".join(self.filter.in_data_types.keys()),
                             ", ".join(remote_node.filter.out_data_types.keys()))

    def disconnected(self, local_term: Terminal, remote_term: Terminal) -> None:
        """Handle behaviour if terminal was disconnected. Removes channel link from filter.

        Could emit signals. See pyqtgraph.flowchart.Node.disconnected().

        Args:
            local_term: The terminal on the node itself.
            remote_term: The terminal of the other node.

        """
        if local_term.isInput() and remote_term.isOutput():
            self.filter.channel_links[local_term.name()] = ""

    def rename(self, name: str) -> None:
        """Handle behaviour if node was renamed. Changes filter.id.

        Could emit signals. See pyqtgraph.flowchart.Node.rename().

        Args:
            name: The new name of the filter.

        Returns:
            The return value of pyqtgraph.flowchart.Node.rename().

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
        for filter_ in filters_to_update:
            for input_key in filter_.channel_links:
                # FIXME the name is not always present
                prefix, suffix = filter_.channel_links[input_key].split(":")
                if prefix == old_name:
                    filter_.channel_links[input_key] = f"{name}:{suffix}"
        super().rename(name)

    def update_filter_pos(self) -> None:
        """Save the node's position inside the ui to the registered filter."""
        pos = self.graphicsItem().pos()
        self._filter.pos = (pos.x(), pos.y())

    @property
    def filter(self) -> Filter:
        """The corresponding filter."""
        return self._filter

    def update_node_after_settings_changed(self) -> None:
        """Re-derive the filter's I/O signature and sync pyqtgraph terminals to match.

        Dynamic-I/O filter subclasses derive their ``in_data_types`` / ``out_data_types``
        from ``filter_configurations`` in :meth:`model.filter.Filter._rebuild_io`. After the
        settings widget commits a configuration change the model dicts are stale until that
        hook re-runs; this method triggers the hook and then diffs the current pyqtgraph
        terminals against the fresh model signature, adding or removing terminals as needed.
        Static-I/O filters produce a stable signature so the diff is a no-op.

        Subclasses may still override for custom behaviour (e.g. preserving user-managed
        extra terminals), but the default now handles the generic rebuild + sync case.
        """
        if self._filter is None:
            return
        self._filter._rebuild_io()
        desired_in = set(self._filter.in_data_types.keys())
        desired_out = set(self._filter.out_data_types.keys())
        for name in list(self.inputs().keys()):
            if name not in desired_in:
                self.removeTerminal(name)
        for name in list(self.outputs().keys()):
            if name not in desired_out:
                self.removeTerminal(name)
        for name in desired_in:
            if name not in self.inputs():
                self.addInput(name)
        for name in desired_out:
            if name not in self.outputs():
                self.addOutput(name)

    @staticmethod
    def _terminals_from_filter(filter_: Filter) -> dict[str, dict[str, str]]:
        """Derive the pyqtgraph ``terminals`` dict from a fully-initialised filter.

        Used by :meth:`__init__` when the subclass does not pass an explicit ``terminals``
        argument. Returns ``{"name": {"io": "in"/"out"}}`` by walking the filter's
        ``in_data_types`` and ``out_data_types``. Returns an empty dict if neither is
        populated yet, which keeps the existing "subclass passes terminals explicitly"
        pattern working for filter types that have not yet been migrated to the
        :mod:`model.filters` subclass hierarchy.
        """
        terminals: dict[str, dict[str, str]] = {}
        for name in filter_.in_data_types:
            terminals[name] = {"io": "in"}
        for name in filter_.out_data_types:
            terminals[name] = {"io": "out"}
        return terminals

    def close(self) -> None:
        """Close the node and remove the linked filter from the scene."""
        self.filter.scene.remove_filter(self.filter)
        super().close()
