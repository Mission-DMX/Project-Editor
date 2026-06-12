"""Contains UIWidget adapter for color director."""
from typing import override

from PySide6.QtWidgets import QDialog, QLabel, QWidget

from model import UIPage, UIWidget
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

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        return ControllerWidget(self.parent.scene.get_filter_by_id(self.filter_ids[0]), self._pending_updates, parent)

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        return ControllerWidget(self.parent.scene.get_filter_by_id(self.filter_ids[0]), None, parent)

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        c = ColorDirectorShowUIWidget(new_parent, self.configuration.copy())
        super().copy_base(c)
        return c

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        return QLabel("Nothing to configure.")
