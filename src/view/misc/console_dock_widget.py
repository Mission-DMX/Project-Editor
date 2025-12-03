"""Dockable terminal widget."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import QDockWidget, QHBoxLayout, QScrollBar, QWidget

from controller.cli.cli_context import CLIContext
from controller.network import NetworkManager
from view.misc.termqt import Terminal, TerminalIO
from view.misc.termqt.terminal_widget import CursorState

if TYPE_CHECKING:
    from PySide6.QtGui import QFocusEvent

    from model import BoardConfiguration


_NEWLINE_CHAR = 13
_BACKSPACE_CHAR = 8


class CLITerminalIO(TerminalIO):
    """Terminal IO implementation to adapter CLIContext."""

    def __init__(self, show: BoardConfiguration, stdout_callback: callable) -> None:
        """Initialize the IO adapter."""
        self._context = CLIContext(show=show, network_manager=NetworkManager())
        self._stdout_callback = stdout_callback
        self._buffer = []

    @override
    def spawn(self) -> None:
        self._stdout_callback(b"> ")

    @override
    def resize(self, rows: int, cols: int) -> None:
        pass  # Do nothing

    @override
    def write(self, buffer: bytes) -> None:
        executed_command = False
        for b in buffer:
            if b == _NEWLINE_CHAR:
                cmd = bytes(self._buffer).decode()
                self._buffer.clear()
                self._context.exec_command(cmd)
                self._stdout_callback(b"\n")
                self._stdout_callback(self._context.fetch_print_buffer().encode())
                executed_command = True
            elif b == _BACKSPACE_CHAR:
                if len(buffer) > 0:
                    self._buffer.pop(-1)
            else:
                self._buffer.append(b)
        self._stdout_callback(buffer)
        if executed_command:
            self._stdout_callback(b"\r\n> ")

    @override
    def terminate(self) -> None:
        pass  # Do nothing

    @override
    def is_alive(self) -> bool:
        return True


class ConsoleDockWidget(QDockWidget):
    """Displays a terminal for the CLI as a QDockWidget."""

    def __init__(self, parent: QWidget, show: BoardConfiguration) -> None:
        """Initialize the widget."""
        super().__init__(parent)
        self._container_widget = QWidget(self)
        layout = QHBoxLayout()
        self._terminal_widget = Terminal(800, 200)
        self._terminal_widget.maximum_line_history = 2500
        layout.addWidget(self._terminal_widget)
        self._scrollbar = QScrollBar(self._container_widget)
        layout.addWidget(self._scrollbar)
        self._terminal_widget.connect_scroll_bar(self._scrollbar)
        layout.setSpacing(0)
        self._container_widget.setLayout(layout)
        self.setWidget(self._container_widget)
        self.setWindowTitle("CLI")
        self._io = CLITerminalIO(show, self._terminal_widget.stdout)
        self._terminal_widget.stdin_callback = self._io.write
        self._terminal_widget.resize_callback = self._io.resize
        self._io.spawn()
        self._scrollbar.setSliderPosition(0)
        self._terminal_widget.setFocus()

    @override
    def focusInEvent(self, event: QFocusEvent, /) -> None:
        super().focusInEvent(event)
        self._terminal_widget.focusWidget()
        if self._terminal_widget._cursor_blinking_state == CursorState.UNFOCUSED:
            self._terminal_widget._cursor_blinking_state = CursorState.ON

    @override
    def focusOutEvent(self, event: QFocusEvent, /) -> None:
        if self._terminal_widget._cursor_blinking_state == CursorState.ON:
            self._terminal_widget._cursor_blinking_state = CursorState.UNFOCUSED
        super().focusOutEvent(event)
