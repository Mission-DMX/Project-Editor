"""Contains methods to generate previews for presets."""

from __future__ import annotations

import atexit
import math
import os
import weakref
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QCoreApplication, QPointF, QThread, Signal
from PySide6.QtGui import QBrush, QImage, QPainter, Qt

from utility import resource_path

if TYPE_CHECKING:
    from PySide6.QtCore import QObject

    from model.color_hsi import ColorHSI
    from model.media_assets.image import AbstractImageAsset
    from model.virtual_filters.colordirector_vfilter import ColorPreset


_DELETION_GRACE_MS = 5000
"""Maximum time in milliseconds __del__ waits for a still running worker before the thread is destroyed."""

_FULL_CIRCLE_SPAN = 360 * 16
"""Pie chart span of a full circle in Qt degrees as expected by QPainter.drawPie."""

_RUNNING_GENERATORS: weakref.WeakSet[PreviewBitmapGenerator] = weakref.WeakSet()
"""Weak references to all generators, so still running workers can be stopped before the interpreter shuts down."""


def _interrupt_running_generators() -> None:
    """Interrupt and wait for all still running workers before the interpreter shuts down."""
    for generator in list(_RUNNING_GENERATORS):
        try:
            if generator.isRunning():
                generator.requestInterruption()
                generator.wait(_DELETION_GRACE_MS)
        except RuntimeError:
            pass


atexit.register(_interrupt_running_generators)


class PreviewBitmapGenerator(QThread):
    """Class to generate previews for presets.

    The thread emits the preset_preview_generated signal for every generated preset. Once the thread is done, the
    built-in finished signal of QThread is emitted and the instance deletes itself.

    """

    preset_preview_generated = Signal(int, QImage)

    def __init__(self, presets: list[ColorPreset], size: int = 32, parent: QObject | None = None) -> None:
        """Initialize using the presets to generate previews for and the preview size in pixels.


        Args:
            presets: The color presets to generate preview images for.
            size: The edge length of the generated preview images in pixels.
            parent: The parent object.

        """
        if parent is None:
            parent = QCoreApplication.instance()
        super().__init__(parent)
        self._render_data: list[tuple[list[ColorHSI], list[list[ColorHSI]], bool, AbstractImageAsset | None]] = [
            (
                preset.get_button_visualization(),
                [step[2] for step in preset.colors],
                len(preset.colors) > 1,
                preset.visualization_asset,
            )
            for preset in presets
        ]
        self._size = size
        self.finished.connect(self.deleteLater)
        _RUNNING_GENERATORS.add(self)

    def __del__(self) -> None:
        """Ensure the worker has stopped before the underlying QThread is destroyed."""
        try:
            if self.isRunning() and QThread.currentThread() is not self:
                self.requestInterruption()
                self.wait(_DELETION_GRACE_MS)
        except (RuntimeError, TypeError):
            pass

    @override
    def run(self) -> None:
        repeat_image = QImage(resource_path(os.path.join("resources", "icons", "repeat.svg")))
        repeat_image = repeat_image.scaled(self._size // 2, self._size // 2)
        for i, (colors, accent_colors, repeats, visualization_asset) in enumerate(self._render_data):
            if self.isInterruptionRequested():
                break
            image = QImage(self._size, self._size, QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(Qt.GlobalColor.transparent)
            p = QPainter(image)
            rect = image.rect()
            num_colors = len(colors)
            last_angle = 0
            arc_size = _FULL_CIRCLE_SPAN // num_colors if num_colors > 0 else 0
            segment_bounds: list[tuple[int, int]] = []
            p.setPen(Qt.PenStyle.NoPen)
            for color_index, color in enumerate(colors):
                p.setBrush(QBrush(color.to_qt_color()))
                span = _FULL_CIRCLE_SPAN - last_angle if color_index == num_colors - 1 else arc_size
                p.drawPie(rect, last_angle, span)
                segment_bounds.append((last_angle, last_angle + span))
                last_angle += span
            self._draw_accent_color_dots(p, accent_colors, segment_bounds)
            if repeats:
                icon_position = self._size - repeat_image.width()
                p.drawImage(icon_position, 0, repeat_image)
            if visualization_asset is not None:
                asset_image = visualization_asset.get_image_for_ui().scaled(self._size, self._size)
                p.drawImage(0, 0, asset_image)
            p.end()
            self.preset_preview_generated.emit(i, image)

    def _draw_accent_color_dots(
        self, painter: QPainter, accent_colors: list[list[ColorHSI]], segment_bounds: list[tuple[int, int]]
    ) -> None:
        """Draw the accent colors of every preset step as little dots evenly spaced on the arc of the segments.

        Args:
            painter: The painter used to draw the preview image. The pie segments are expected to be drawn
                already.
            accent_colors: The accent colors of every preset step.
            segment_bounds: The start and end angle of every pie segment in Qt degrees.
        """
        painter.setPen(Qt.PenStyle.NoPen)
        dot_radius = max(2, self._size // 12)
        dot_distance = self._size * 0.4
        center = self._size / 2
        for step_index, step_accent_colors in enumerate(accent_colors):
            if step_index >= len(segment_bounds) or len(step_accent_colors) == 0:
                continue
            start_angle, end_angle = segment_bounds[step_index]
            margin = (end_angle - start_angle) // 8
            first_angle = float(start_angle + margin)
            last_angle = float(end_angle - margin)
            dot_count = len(step_accent_colors)
            if dot_count == 1:
                angles = [first_angle]
            else:
                angles = [first_angle + k * (last_angle - first_angle) / (dot_count - 1) for k in range(dot_count)]
            for dot_index, accent_color in enumerate(step_accent_colors):
                radians = math.radians(angles[dot_index] / 16)
                position = QPointF(
                    center + dot_distance * math.cos(radians),
                    center + dot_distance * math.sin(radians),
                )
                painter.setBrush(QBrush(accent_color.to_qt_color()))
                painter.drawEllipse(position, dot_radius, dot_radius)
