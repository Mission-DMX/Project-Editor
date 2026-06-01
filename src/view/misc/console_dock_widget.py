"""Dockable terminal widget."""

from __future__ import annotations

import atexit
import os
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
_ESCAPE_CHAR = 27
_ESC_UP_CHAR = 65
_ESC_DOWN_CHAR = 66
_ESC_RIGHT_CHAR = 67
_ESC_LEFT_CHAR = 68
_ESC_SEQUENCE_CHAR = 91


_HISTORY_STORAGE_PATH = os.path.join(os.path.expanduser("~"), ".local", "share", "missionDMX")
_HISTORY_STORAGE_FILE = os.path.join(_HISTORY_STORAGE_PATH, "cli_history.list")

if not os.path.exists(_HISTORY_STORAGE_PATH):
    os.makedirs(_HISTORY_STORAGE_PATH, mode=0o770, exist_ok=True)

if not os.path.exists(_HISTORY_STORAGE_FILE):
    with open(_HISTORY_STORAGE_FILE, "w") as f:
        f.write("")
with open(_HISTORY_STORAGE_FILE, "r") as f:
    _history = []
    for line in f.readlines():
        line = line.replace("\n", "").strip()
        if len(line) > 0:
            _history.append(line)
del f


def _write_history() -> None:
    global _history
    if len(_history) > 10000:
        _history = _history[:10000]
    with open(_HISTORY_STORAGE_FILE, "w") as f:
        for h_entry in _history:
            if h_entry.strip() != "":
                f.write(h_entry + "\n")
atexit.register(_write_history)


class CLITerminalIO(TerminalIO):
    """Terminal IO implementation to adapter CLIContext."""

    def __init__(self, show: BoardConfiguration, terminal: Terminal, clear_span: int) -> None:
        """Initialize the IO adapter."""
        self._clear_span = clear_span
        self._context = CLIContext(show=show, network_manager=NetworkManager())
        self._stdout_callback = terminal.stdout
        self._buffer = []
        terminal.stdin_callback = self.write
        terminal.resize_callback = self.resize
        self.spawn()
        self._history_cursor = 0
        self._history_cmd_stash = ""
        self._in_escape = False
        self._cursor_in_buffer = 0

    @override
    def spawn(self) -> None:
        self._stdout_callback(b"\n" * self._clear_span)
        self._stdout_callback(b"> ")

    @override
    def resize(self, rows: int, cols: int) -> None:
        pass  # Do nothing

    @override
    def write(self, buffer: bytes) -> None:
        executed_command = False
        execution_successful = True
        supress_echo = False
        # TODO implement tab completion here
        for b in buffer:
            if b == _NEWLINE_CHAR:
                cmd = bytes(self._buffer).decode().strip()
                self._buffer.clear()
                if len(cmd) > 0:
                    _history.append(cmd)
                execution_successful = self._context.exec_command(cmd)
                self._stdout_callback(b"\n")
                self._stdout_callback(self._context.fetch_print_buffer().encode())
                executed_command = True
                self._history_cursor = 0
            elif b == _BACKSPACE_CHAR:
                self._stdout_callback(bytes([8, ord(" ")] if self._cursor_in_buffer == 0 else [8]))
                if len(buffer) > 0:
                    try:
                        self._buffer.pop(-1)
                    except IndexError:
                        pass  # Simply catching this exception is cheaper than sync
            elif b == _ESCAPE_CHAR:
                self._in_escape = True
                supress_echo = True
            elif self._in_escape and b == _ESC_SEQUENCE_CHAR:
                pass
            elif self._in_escape and b == _ESC_UP_CHAR:
                if len(_history) <= (self._history_cursor + 1):
                    self._in_escape = False
                    continue
                if self._history_cursor == 0:
                    self._history_cmd_stash = bytes(self._buffer).decode()
                self._history_cursor += 1
                self._stdout_callback(b"\r  ")
                self._stdout_callback(bytes([ord(" ")] * len(self._buffer)))
                self._stdout_callback(b"\r> ")
                next_cmd = _history[-1 * self._history_cursor].encode()
                self._stdout_callback(next_cmd)
                self._buffer.clear()
                self._buffer.extend(next_cmd)
                self._in_escape = False
                self._cursor_in_buffer = 0
            elif self._in_escape and b == _ESC_DOWN_CHAR:
                if self._history_cursor == 0:
                    self._in_escape = False
                    continue
                self._history_cursor -= 1
                self._stdout_callback(b"\r> ")
                self._stdout_callback(bytes([ord(" ")] * len(self._buffer)))
                self._stdout_callback(b"\r> ")
                if self._history_cursor == 0:
                    next_buffer = self._history_cmd_stash
                else:
                    next_buffer = _history[-1 * self._history_cursor]
                next_buffer = next_buffer.encode()
                self._stdout_callback(next_buffer)
                self._buffer.clear()
                self._buffer.extend(next_buffer)
                self._in_escape = False
                self._cursor_in_buffer = 0
            elif self._in_escape and b == _ESC_LEFT_CHAR:
                if self._cursor_in_buffer == len(self._buffer):
                    self._in_escape = False
                    continue
                self._cursor_in_buffer += 1
                self._stdout_callback(bytes([_ESCAPE_CHAR, _ESC_SEQUENCE_CHAR, _ESC_LEFT_CHAR]))
                self._in_escape = False
            elif self._in_escape and b == _ESC_RIGHT_CHAR:
                if self._cursor_in_buffer == 0:
                    self._in_escape = False
                    continue
                self._cursor_in_buffer -= 1
                self._stdout_callback(bytes([_ESCAPE_CHAR, _ESC_SEQUENCE_CHAR, _ESC_RIGHT_CHAR]))
                self._in_escape = False
            else:
                self._buffer.insert(len(self._buffer) - self._cursor_in_buffer, b)
        if not supress_echo:
            self._stdout_callback(buffer)
            if self._cursor_in_buffer > 0:
                b = bytes(self._buffer[len(self._buffer) - self._cursor_in_buffer:])
                self._stdout_callback(b)
                self._stdout_callback(
                    bytes([_ESCAPE_CHAR, _ESC_SEQUENCE_CHAR, _ESC_LEFT_CHAR] * self._cursor_in_buffer)
                )
        if executed_command:
            if execution_successful:
                self._stdout_callback(b"\r\n> ")
            else:
                self._stdout_callback(b"\r\n[ERR] > ")

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
        # TODO add select display here
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
        self._io = CLITerminalIO(show, self._terminal_widget, 200)
        self._scrollbar.setSliderPosition(0)
        self._terminal_widget.setFocus()
        # FIXME scroll to top

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
