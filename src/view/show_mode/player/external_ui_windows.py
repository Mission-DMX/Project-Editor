from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import PySide6
from PySide6.QtWidgets import QDialog, QApplication, QVBoxLayout

from controller.network import NetworkManager
from model import Broadcaster
from view.show_mode.player.ui_player_widget import UIPlayerWidget

if TYPE_CHECKING:
    from model import BoardConfiguration

logger = getLogger(__name__)


class _ExternalUIWindow(QDialog):
    def __init__(self, window_index: int, show: BoardConfiguration, parent=None):
        super().__init__(parent)
        self._show = show
        self.setWindowFlag(PySide6.QtCore.Qt.WindowFlags.WindowCloseButtonHint, False)
        self.setWindowFlag(PySide6.QtCore.Qt.WindowFlags.Tool | PySide6.QtCore.Qt.WindowStaysOnTopHint | PySide6.QtCore.Qt.WindowDoesNotAcceptFocus)
        self.setMinimumSize(800, 600)
        self.setWindowTitle(f"External Window {window_index}")
        screens = QApplication.screens()
        screen = screens[(window_index + 1) % len(screens)]
        self.move(screen.geometry().topLeft())
        self._player_widget = UIPlayerWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(self._player_widget)
        self.setLayout(layout)
        self._switched_to_scene(NetworkManager().current_active_scene_id)
        Broadcaster().active_scene_switched.connect(self._switched_to_scene)
        # TODO implement ui page per scene retention mechanism

    def _switched_to_scene(self, new_scene_index: int):
        try:
            self._player_widget.scene = self._show.scenes[new_scene_index]
        except IndexError:
            logger.error(f"Scene {new_scene_index} does not exist in current loaded show file.")

_current_open_windows: list[_ExternalUIWindow] = []

def update_window_count(target: int, show: BoardConfiguration) -> None:
    """Set the amount of external UI windows.

    This method opens or closes the external UI windows according to the requested amount.
    Note:
        This method does not update the show file ui hints.

    Args:
        target: The amount of external UI windows.
    """
    if target < 0:
        raise ValueError("Show UI window count target must be >= 0.")
    while len(_current_open_windows) > target:
        window_to_remove = _current_open_windows[-1]
        window_to_remove.close()
        window_to_remove.deleteLater()
        _current_open_windows.remove(window_to_remove)
    while len(_current_open_windows) < target:
        new_window = _ExternalUIWindow(len(_current_open_windows), show)
        _current_open_windows.append(new_window)
        new_window.showMaximized()
