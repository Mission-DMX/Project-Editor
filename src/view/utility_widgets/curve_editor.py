# coding=utf-8
"""This file contains a widget that allows the editing and visualization of parameters of a trigonometric curve."""
from enum import IntFlag

from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from PySide6.QtGui import QPaintEvent


class BaseCurve(IntFlag):
    """This enum defines which parts should be present in the wave. If multiple apply, they'll be added or multiplied,
    depending on the accumulation selection."""
    SIN = 1
    COS = 2
    TAN = 4
    ARC_SIN = 8
    ARC_COS = 16
    ARC_TAN = 32
    SAWTOOTH = 64
    RECT = 128
    TRIANGLE = 256


class _WaveRenderer(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

    def paintEvent(self, event: "QPaintEvent"):
        p = QPainter(self)

        p.end()


class CurveEditorWidget(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        layout = QVBoxLayout()

        self._renderer = _WaveRenderer(self)
        layout.addWidget(self._renderer)
        self._function_property_container = QTabWidget(self)
        layout.addWidget(self._function_property_container)

        self.setLayout(layout)
