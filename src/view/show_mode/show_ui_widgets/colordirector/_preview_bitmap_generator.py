"""Contains methods to generate previews for presets."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QBrush, QImage, QPainter, QPixmap, Qt

from utility import resource_path

if TYPE_CHECKING:
    from PySide6.QtCore import QObject

    from model.virtual_filters.colordirector_vfilter import ColorPreset


class PreviewBitmapGenerator(QThread):
    """Class to generate previews for presets.

    The runner will call the preset_preview_generated for every generated preset and will call finished once it is
    finished and can be deleted.

    """

    preset_preview_generated = Signal(int, QPixmap)

    def __init__(self, presets: list[ColorPreset], size: int = 32, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._presets = presets
        self._size = size

    @override
    def run(self) -> None:
        repeat_image = QImage(resource_path(os.path.join("resources", "icons", "repeat.svg")))
        repeat_image = repeat_image.scaled(int(self._size * 0.5), int(self._size * 0.5))
        for i, preset in enumerate(self._presets):
            pixmap = QPixmap(self._size, self._size)
            pixmap.fill(Qt.GlobalColor.transparent)
            p = QPainter(pixmap)
            rect = pixmap.rect()
            colors = preset.get_button_visualization()
            num_colors = len(colors)
            last_angle = 0
            arc_size = int((360 * 16) / num_colors)
            p.setPen(Qt.PenStyle.NoPen)
            for color in colors:
                p.setBrush(QBrush(color.to_qt_color()))
                p.drawPie(rect, last_angle, arc_size)
                last_angle += arc_size
            if len(preset.colors) > 1:
                p.drawImage(int(self._size * 0.55), 0, repeat_image)
            visualization_asset = preset.visualization_asset
            if visualization_asset is not None:
                image = visualization_asset.get_image_for_ui().scaled(self._size, self._size)
                p.drawImage(0, 0, image)
            p.end()
            self.preset_preview_generated.emit(i, pixmap)
        self.finished.emit()
