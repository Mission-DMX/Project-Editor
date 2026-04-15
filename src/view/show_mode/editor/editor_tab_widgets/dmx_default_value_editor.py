"""Contains DMX default value editor tab widget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from model.scene import Scene

class DMXDefaultValueEditorWidget(QWidget):
    def __init__(self, scene: Scene, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene: Scene = scene

    @property
    def scene(self) -> Scene:
        return self._scene
