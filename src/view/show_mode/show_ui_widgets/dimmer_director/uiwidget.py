"""Runtime UI widget adapter for the Dimmer Director filter."""

from __future__ import annotations

from typing import override

from PySide6.QtWidgets import QDialog, QLabel, QWidget

from model import UIPage, UIWidget
from model.filters.dimmer_director import DimmerDirectorFilter

from ._controller_widget import ControllerWidget


class DimmerDirectorShowUIWidget(UIWidget):
    """Show-mode UI widget wrapping a ``DimmerDirectorFilter``."""

    def __init__(self, parent_page: UIPage, configuration: dict[str, str] | None = None) -> None:
        """Initialize the widget and allocate the pending-updates queue."""
        super().__init__(parent_page, configuration)
        self._pending_updates: list[tuple[str, str]] = []

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        """Return and clear the list of pending update messages."""
        copied = self._pending_updates.copy()
        self._pending_updates.clear()
        return copied

    def _get_linked_filter(self) -> DimmerDirectorFilter | None:
        """Resolve the linked filter if one is attached and of the expected type."""
        if len(self.filter_ids) == 0:
            return None
        linked = self.parent.scene.get_filter_by_id(self.filter_ids[0])
        if not isinstance(linked, DimmerDirectorFilter):
            return None
        return linked

    @staticmethod
    def _missing_filter_widget(parent: QWidget | None) -> QWidget:
        """Build a placeholder widget shown when the linked filter is missing."""
        label = QLabel("The linked dimmer director filter is missing.", parent)
        label.setWordWrap(True)
        return label

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        """Return the runtime controller widget with feedback highlighting enabled."""
        linked = self._get_linked_filter()
        if linked is None:
            return self._missing_filter_widget(parent)
        controller = ControllerWidget(linked, self._pending_updates, feedback_enabled=True, parent=parent)
        controller.update_requested.connect(self.push_update)
        return controller

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        """Return the controller widget in read-only configuration mode."""
        linked = self._get_linked_filter()
        if linked is None:
            return self._missing_filter_widget(parent)
        return ControllerWidget(linked, None, feedback_enabled=False, parent=parent)

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        """Shallow-copy the widget onto a new UI page."""
        copied = DimmerDirectorShowUIWidget(new_parent, self.configuration.copy())
        super().copy_base(copied)
        return copied

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        """Return a placeholder for the configuration dialog (no per-instance options yet)."""
        return QLabel("Nothing to configure.", parent)
