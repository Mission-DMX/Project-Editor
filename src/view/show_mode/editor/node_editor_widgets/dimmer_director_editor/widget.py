"""Configuration widget for the Dimmer Director filter."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import QMessageBox, QTabWidget, QWidget

from model.filters.dimmer_director import DimmerDirectorFilter
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget

from ._curves_tab import CurvesTab
from ._global_inputs_tab import GlobalInputsTab
from ._groups_tab import GroupsTab
from ._recalls_tab import RecallsTab

if TYPE_CHECKING:
    from model import Filter
    from view.show_mode.editor.nodes import FilterNode

logger = getLogger(__name__)


class DimmerDirectorEditorWidget(NodeEditorFilterConfigWidget):
    """QTabWidget-based editor with Global Inputs, Groups, Curves and Recalls tabs."""

    def __init__(self, model: Filter, parent: QWidget | None = None) -> None:
        """Build the four tabs and lock the UI if the loaded format version is unsupported."""
        super().__init__()
        if not isinstance(model, DimmerDirectorFilter):
            raise TypeError("Dimmer Director filter must be a DimmerDirectorFilter.")
        self._model: DimmerDirectorFilter = model
        self._widget = QTabWidget(parent)
        self._widget.setMinimumWidth(900)

        self._global_tab = GlobalInputsTab(self._model, self._widget)
        self._widget.addTab(self._global_tab, "Global Inputs")

        self._groups_tab = GroupsTab(self._model, self._widget)
        self._widget.addTab(self._groups_tab, "Groups")

        self._curves_tab = CurvesTab(self._model, self._widget)
        self._widget.addTab(self._curves_tab, "Curves")

        self._recalls_tab = RecallsTab(self._model, self._widget)
        self._groups_tab.groups_changed.connect(self._recalls_tab.update_recall_table)
        self._curves_tab.curves_changed.connect(self._recalls_tab.update_recall_table)
        self._widget.addTab(self._recalls_tab, "Recalls")

        if not self._model.configuration_format_supported:
            self._widget.setEnabled(False)
            self._show_unsupported_format_error_box()
        self._error_box: QMessageBox | None = None

    @override
    def _get_configuration(self) -> dict[str, str]:
        self._curves_tab.apply_pending_resample()
        self._model.serialize_to_configuration()
        return {}

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        """Model owns the state; nothing additional to load from the parameters dict."""

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> None:
        """Nothing to do: the model's parameters are managed by the model directly."""

    @override
    def _get_parameters(self) -> dict[str, str]:
        self._curves_tab.apply_pending_resample()
        self._model.serialize_to_configuration()
        return self._model.initial_parameters

    @override
    def parent_opened(self) -> None:
        """No special action required when the dialog opens."""

    @override
    def parent_closed(self, filter_node: FilterNode) -> None:
        """Flush any pending keyframe edits and persist the serialized configuration."""
        self._curves_tab.apply_pending_resample()
        self._model.serialize_to_configuration()
        super().parent_closed(filter_node)

    def _show_unsupported_format_error_box(self) -> None:
        """Inform the user that the loaded configuration format is newer than this editor."""
        self._error_box = QMessageBox(self._widget)
        self._error_box.setWindowTitle("Unsupported Configuration Format")
        self._error_box.setText(
            "The configuration of this dimmer director was written using a newer, unsupported format version. "
            "Its data is preserved within the show file and editing is disabled. Update the editor to edit "
            "this filter.",
        )
        self._error_box.setIcon(QMessageBox.Icon.Critical)
        self._error_box.show()
