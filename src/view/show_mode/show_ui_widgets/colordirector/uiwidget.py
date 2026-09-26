"""Contains UIWidget adapter for color director."""

from typing import override

from PySide6.QtWidgets import QDialog, QLabel, QWidget

from model import UIPage, UIWidget
from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter
from view.show_mode.show_ui_widgets.colordirector._controller_widget import ControllerWidget


class ColorDirectorShowUIWidget(UIWidget):
    """Handles show UI widget interface for color director."""

    def __init__(self, parent_page: UIPage, configuration: dict[str, str] | None = None) -> None:
        """Initializes ColorDirectorShowUIWidget."""
        super().__init__(parent_page, configuration)
        self._pending_updates: list[tuple[str, str]] = []

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        copied_list = self._pending_updates.copy()
        self._pending_updates.clear()
        return copied_list

    def _get_linked_filter(self) -> ColordirectorVFilter | None:
        """Get the color director filter linked to this widget.

        Returns:
            The linked color director filter. None if no filter is linked or the linked filter is missing or of an
            unexpected type.

        """
        if len(self.filter_ids) == 0:
            return None
        linked_filter = self.parent.scene.get_filter_by_id(self.filter_ids[0])
        if not isinstance(linked_filter, ColordirectorVFilter):
            return None
        return linked_filter

    @staticmethod
    def _generate_missing_filter_widget(parent: QWidget | None) -> QWidget:
        """Generate a placeholder widget informing about a missing linked filter.

        Args:
            parent: The parent of the generated placeholder widget.

        Returns:
            A label informing the user that the linked color director filter is missing.

        """
        label = QLabel("The linked color director filter is missing.", parent)
        label.setWordWrap(True)
        return label

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        linked_filter = self._get_linked_filter()
        if linked_filter is None:
            return self._generate_missing_filter_widget(parent)
        controller = ControllerWidget(linked_filter, self._pending_updates, feedback_enabled=True, parent=parent)
        controller.update_requested.connect(self.push_update)
        return controller

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        linked_filter = self._get_linked_filter()
        if linked_filter is None:
            return self._generate_missing_filter_widget(parent)
        return ControllerWidget(linked_filter, None, feedback_enabled=False, parent=parent)

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        c = ColorDirectorShowUIWidget(new_parent, self.configuration.copy())
        super().copy_base(c)
        return c

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        return QLabel("Nothing to configure.")
