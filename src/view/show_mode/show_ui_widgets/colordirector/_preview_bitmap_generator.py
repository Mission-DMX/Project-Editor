"""Contains methods to generate previews for presets."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QBrush, QImage, QPainter, Qt

from utility import resource_path

if TYPE_CHECKING:
    from PySide6.QtCore import QObject

    from model.virtual_filters.colordirector_vfilter import ColorPreset


_DELETION_GRACE_MS = 5000
"""Maximum time in milliseconds __del__ waits for a still running worker before the thread is destroyed."""


class PreviewBitmapGenerator(QThread):
    """Class to generate previews for presets.

    The runner will call the preset_preview_generated signal for every generated preset. Once the thread is done, the
    built-in finished signal of QThread is emitted and the instance may be deleted."""

    preset_preview_generated = Signal(int, QImage)

    def __init__(self, presets: list[ColorPreset], size: int = 32, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._presets = presets
        self._size = size

    def __del__(self) -> None:
        """Ensure the worker has stopped before the underlying QThread is destroyed."""
        try:
            if self.isRunning():
                self.requestInterruption()
                self.wait(_DELETION_GRACE_MS)
        except RuntimeError:
            pass

    @override
    def run(self) -> None:
        repeat_image = QImage(resource_path(os.path.join("resources", "icons", "repeat.svg")))
        repeat_image = repeat_image.scaled(int(self._size * 0.5), int(self._size * 0.5))
        for i, preset in enumerate(self._presets):
            if self.isInterruptionRequested():
                break
            image = QImage(self._size, self._size, QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(Qt.GlobalColor.transparent)
            p = QPainter(image)
            rect = image.rect()
            colors = preset.get_button_visualization()
            num_colors = len(colors)
            last_angle = 0
            arc_size = int((360 * 16) / num_colors) if num_colors > 0 else 0
            p.setPen(Qt.PenStyle.NoPen)
            for color in colors:
                p.setBrush(QBrush(color.to_qt_color()))
                p.drawPie(rect, last_angle, arc_size)
                last_angle += arc_size
            # TODO for each accent color in in the preset draw a little dot evenly spaced on the arc
            if len(preset.colors) > 1:
                p.drawImage(int(self._size * 0.55), 0, repeat_image)
            visualization_asset = preset.visualization_asset
            if visualization_asset is not None:
                asset_image = visualization_asset.get_image_for_ui().scaled(self._size, self._size)
                p.drawImage(0, 0, asset_image)
            p.end()
            self.preset_preview_generated.emit(i, image)
