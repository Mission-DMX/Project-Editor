"""Contains spin box implementation supporting jog wheel."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox

from model import Broadcaster

if TYPE_CHECKING:
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QAbstractSpinBox, QWidget

    _JogwheelSpinBoxBase = QAbstractSpinBox
else:
    _JogwheelSpinBoxBase = object


class _JogwheelInputMixin(_JogwheelSpinBoxBase):
    """Mixin adding jog wheel input and enter key value submission to spin boxes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the spin box and connect the jog wheel rotation signals of the broadcaster.

        Jog wheel rotation events are only processed while the spin box has the keyboard focus.

        """
        super().__init__(parent)
        self._broadcaster = Broadcaster()
        self._broadcaster.jogwheel_rotated_left.connect(self._jg_down)
        self._broadcaster.jogwheel_rotated_right.connect(self._jg_up)
        self.destroyed.connect(self._disconnect_from_broadcaster)
        # TODO also trigger value_submitted if in focus and xtouch enter pressed

    def _disconnect_from_broadcaster(self) -> None:
        """Disconnect the jog wheel rotation signals when the spin box is destroyed."""
        try:
            self._broadcaster.jogwheel_rotated_left.disconnect(self._jg_down)
            self._broadcaster.jogwheel_rotated_right.disconnect(self._jg_up)
        except RuntimeError:
            # the connections have already been removed, e.g. by Qt while destroying the spin box
            pass

    def _submit_value(self) -> None:
        """Submit the current value. Implemented by the class using this mixin."""
        raise NotImplementedError

    @override
    def keyPressEvent(self, event: QKeyEvent, /) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.hasFocus():
            self.interpretText()
            self._submit_value()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _jg_down(self) -> None:
        if self.hasFocus():
            self.stepBy(-1)

    def _jg_up(self) -> None:
        if self.hasFocus():
            self.stepBy(1)


class JogwheelSpinBox(_JogwheelInputMixin, QSpinBox):
    """Spin box supporting jog wheel input.

    If the user presses enter while editing, the value_submitted signal will be emitted.

    """

    value_submitted = Signal(int)

    def _submit_value(self) -> None:
        """Emit the current value using the value_submitted signal."""
        self.value_submitted.emit(self.value())


class JogwheelDoubleSpinBox(_JogwheelInputMixin, QDoubleSpinBox):
    """Double spin box supporting jog wheel input.

    If the user presses enter while editing, the value_submitted signal will be emitted.

    """

    value_submitted = Signal(float)

    def _submit_value(self) -> None:
        """Emit the current value using the value_submitted signal."""
        self.value_submitted.emit(self.value())
