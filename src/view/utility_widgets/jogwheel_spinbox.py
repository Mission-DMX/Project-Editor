"""Contains spin box implementation supporting jog wheel."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QSpinBox

from model import Broadcaster

if TYPE_CHECKING:
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QWidget

class JogwheelSpinBox(QSpinBox):
    """QSpinBox implementation supporting jog wheel and enter key causing action.

    If the user presses enter while editing, the value_submitted signal will be emitted.

    """

    value_submitted = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize just like QSpinBox."""
        super().__init__(parent)
        self._broadcaster = Broadcaster()
        self._broadcaster.jogwheel_rotated_left.connect(self._jg_down)
        self._broadcaster.jogwheel_rotated_right.connect(self._jg_up)

    @override
    def keyPressEvent(self, event: QKeyEvent, /) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.hasFocus():
            self.value_submitted.emit(self.value())
            event.accept()
        else:
            super().keyPressEvent(event)

    def _jg_down(self) -> None:
        if self.hasFocus():
            val = self.value() - self.singleStep()
            if val >= self.minimum():
                self.setValue(val)

    def _jg_up(self) -> None:
        if self.hasFocus():
            val = self.value() + self.singleStep()
            if val >= self.maximum():
                self.setValue(val)
