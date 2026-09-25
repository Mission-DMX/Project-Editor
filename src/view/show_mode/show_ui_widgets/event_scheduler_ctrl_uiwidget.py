"""Contains UI Widget for control of event scheduler."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from model import UIWidget

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog, QWidget

    from model import UIPage


class EventSchedulerCtrlUIWidget(UIWidget):
    """Event scheduler control widget.

    This widget allows the user to override the event scheduler parameters live.
    It provides a matrix editor for triggers, buttons to control the number of steps, and a spin box to override the
    default step.

    In the future, a mechanism to enable/disaable the advancement es well as a method to override the synchronization
    event might be added.

    """

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize the UI widget."""
        super().__init__(parent, configuration)

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        pass  # TODO

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        pass  # TODO

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        pass  # TODO

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        pass  # TODO

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        pass  # TODO
