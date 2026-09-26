"""Contains methods to generate previews for presets."""

from __future__ import annotations

import atexit
import math
import os
import weakref
from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QCoreApplication, QPointF, QThread, Signal
from PySide6.QtGui import QBrush, QImage, QPainter, Qt

from utility import resource_path

if TYPE_CHECKING:
    from PySide6.QtCore import QObject

    from model.color_hsi import ColorHSI
    from model.media_assets.image import AbstractImageAsset
    from model.virtual_filters.colordirector_vfilter import ColorPreset

logger = getLogger(__name__)

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
            size: The edge length of the generated preview images in pixels. It must be at least two pixels.
            parent: The parent object.

        Raises:
            ValueError: If the provided size is smaller than two pixels.

        """
        if size < 2:
            raise ValueError("The preview size must be at least two pixels.")
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
        """Generate a preview image for every color preset.

        Every preview consists of pie segments visualizing the colors of the preset steps, accent color dots drawn
        onto the segments, an icon marking repeating presets and the visualization asset if one is set. The
        generated images are provided using the preset_preview_generated signal. The generation stops before the
        current preset if an interruption was requested using requestInterruption.

        """
        repeat_image: QImage | None = None
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
                if repeat_image is None:
                    repeat_image = self._load_repeat_image()
                if repeat_image is not None:
                    icon_position = self._size - repeat_image.width()
                    p.drawImage(icon_position, 0, repeat_image)
            if visualization_asset is not None:
                asset_image = visualization_asset.get_image_for_ui()
                if asset_image is None or asset_image.isNull():
                    logger.warning("The visualization asset of preset %i provides no loadable image: Skipped.", i)
                else:
                    p.drawImage(0, 0, asset_image.scaled(self._size, self._size))
            p.end()
            self.preset_preview_generated.emit(i, image)

    def _load_repeat_image(self) -> QImage | None:
        """Load the icon marking repeating presets.

        Returns:
            The scaled repeat icon or None if the icon file could not be loaded: Presets are generated without the
            icon instead of breaking the preview generation.

        """
        icon_path = resource_path(os.path.join("resources", "icons", "repeat.svg"))
        icon_image = QImage(icon_path)
        if icon_image is None or icon_image.isNull():
            logger.warning("The repeat icon '%s' could not be loaded: Presets are generated without it.", icon_path)
            return None
        return icon_image.scaled(self._size // 2, self._size // 2)

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
