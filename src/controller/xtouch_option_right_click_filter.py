"""Global event filter that translates left-clicks to right-clicks while the XTouch Option key is held.

The editor is often used on a touchscreen with an XTouch control surface attached. Touch generates
left-button events, which makes it impossible to open right-click context menus. Holding the XTouch
Option button (``BTN_OPTION``) while tapping routes the gesture through this filter, which synthesizes
a right-button press/move/release sequence and posts a ``QContextMenuEvent`` on release.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QContextMenuEvent, QMouseEvent
from PySide6.QtWidgets import QApplication


class XTouchOptionRightClickFilter(QObject):
    """Singleton QApplication-level event filter for Option+click → right-click translation."""

    _instance: XTouchOptionRightClickFilter | None = None

    @classmethod
    def instance(cls) -> XTouchOptionRightClickFilter:
        """Return the singleton instance, creating it on first use."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        """Initialize internal state. Do not call directly; use :meth:`instance`."""
        super().__init__()
        self._option_held: bool = False
        # Latched between a translated press and its matching release so that releasing Option
        # mid-click still produces a well-formed right-release + QContextMenuEvent.
        self._in_sequence: bool = False
        # Re-entrance guard: QApplication.sendEvent delivers through the filter again.
        self._dispatching: bool = False

    def set_option_held(self, held: bool) -> None:
        """Update the Option-held state. Called by the XTouch network event handler."""
        self._option_held = held

    def eventFilter(self, obj: QObject, ev: QEvent) -> bool:
        """Translate left mouse events to right mouse events while Option is held / latched."""
        t = ev.type()
        if t not in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.MouseMove):
            return False
        if self._dispatching:
            return False
        if not self._option_held and not self._in_sequence:
            return False
        if not isinstance(ev, QMouseEvent):
            return False
        if ev.button() == Qt.MouseButton.RightButton or (ev.buttons() & Qt.MouseButton.RightButton):
            return False

        if t == QEvent.Type.MouseButtonPress and ev.button() == Qt.MouseButton.LeftButton and self._option_held:
            self._in_sequence = True
            self._redispatch_mouse(obj, ev, QEvent.Type.MouseButtonPress,
                                   Qt.MouseButton.RightButton, Qt.MouseButton.RightButton)
            return True
        if t == QEvent.Type.MouseMove and self._in_sequence:
            self._redispatch_mouse(obj, ev, QEvent.Type.MouseMove,
                                   Qt.MouseButton.NoButton, Qt.MouseButton.RightButton)
            return True
        if t == QEvent.Type.MouseButtonRelease and ev.button() == Qt.MouseButton.LeftButton and self._in_sequence:
            self._redispatch_mouse(obj, ev, QEvent.Type.MouseButtonRelease,
                                   Qt.MouseButton.RightButton, Qt.MouseButton.NoButton)
            self._post_context_menu(obj, ev)
            self._in_sequence = False
            return True
        return False

    def _redispatch_mouse(self, receiver: QObject, src: QMouseEvent, etype: QEvent.Type,
                          button: Qt.MouseButton, buttons: Qt.MouseButton) -> None:
        new_ev = QMouseEvent(
            etype,
            src.position(),
            src.scenePosition(),
            src.globalPosition(),
            button,
            buttons,
            src.modifiers(),
            src.pointingDevice(),
        )
        self._dispatching = True
        try:
            QApplication.sendEvent(receiver, new_ev)
        finally:
            self._dispatching = False

    def _post_context_menu(self, receiver: QObject, src: QMouseEvent) -> None:
        cm = QContextMenuEvent(
            QContextMenuEvent.Reason.Mouse,
            src.position().toPoint(),
            src.globalPosition().toPoint(),
            src.modifiers(),
        )
        self._dispatching = True
        try:
            QApplication.sendEvent(receiver, cm)
        finally:
            self._dispatching = False
