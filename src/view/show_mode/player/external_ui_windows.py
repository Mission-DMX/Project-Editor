from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import PySide6
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout

from controller.network import NetworkManager
from model import Broadcaster
from view.show_mode.player.ui_player_widget import UIPlayerWidget

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from model import BoardConfiguration

logger = getLogger(__name__)


class _ExternalUIWindow(QDialog):
    """Non-Focus window to display additional show UI pages."""

    def __init__(self, window_index: int, show: BoardConfiguration, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._show = show
        self._window_index = window_index
        self.setWindowFlag(PySide6.QtCore.Qt.WindowFlags.WindowCloseButtonHint, False)
        self.setWindowFlag(
            PySide6.QtCore.Qt.WindowFlags.Tool |
            PySide6.QtCore.Qt.WindowStaysOnTopHint |
            PySide6.QtCore.Qt.WindowDoesNotAcceptFocus
        )
        self.setMinimumSize(800, 600)
        self.setWindowTitle(f"External Window {window_index}")
        screens = QApplication.screens()
        screen = screens[(window_index + 1) % len(screens)]
        self.move(screen.geometry().topLeft())
        self._player_widget = UIPlayerWidget(self)
        self._player_widget.selected_page_changed.connect(self._player_changed_page)
        layout = QVBoxLayout()
        layout.addWidget(self._player_widget)
        self.setLayout(layout)
        self._switched_to_scene(NetworkManager().current_active_scene_id)
        Broadcaster().active_scene_switched.connect(self._switched_to_scene)

    def _switched_to_scene(self, new_scene_index: int) -> None:
        try:
            self._player_widget.selected_page_changed_locked = True
            previous_page_index = self._get_page_index_by_scene(new_scene_index)
            self._player_widget.scene = self._show.scenes[new_scene_index]
            self._player_widget.goto_page(previous_page_index)
            QApplication.processEvents()
            self._player_widget.selected_page_changed_locked = False
            logger.debug("Scene switch in ui window %s to %s", self._window_index, new_scene_index)
        except IndexError:
            logger.error("Scene %s does not exist in current loaded show file.", new_scene_index)

    def _player_changed_page(self, new_index: int) -> None:
        window_indices = self._parse_indicies_hint()
        current_scene_index = NetworkManager().current_active_scene_id
        while len(window_indices) <= current_scene_index:
            window_indices.append(0)
        window_indices[current_scene_index] = new_index
        self._show.ui_hints[f"show_ui_window::{self._window_index}"] = ";".join([str(i) for i in window_indices])
        logger.debug("Player changed page to page %s. Hints were updated.", new_index)


    def _get_page_index_by_scene(self, new_scene_index: int) -> int:
        window_indices = self._parse_indicies_hint()
        if new_scene_index >= len(window_indices):
            return 0
        return window_indices[new_scene_index]

    def _parse_indicies_hint(self) -> list[int]:
        hint = self._show.ui_hints.get(f"show_ui_window::{self._window_index}", "")
        if len(hint) == 0:
            return []
        return [int(ss) for ss in hint.split(";")]


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
