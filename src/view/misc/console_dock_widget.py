"""Dockable terminal widget."""

from __future__ import annotations

import atexit
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING, Final, override

from PySide6.QtWidgets import QDockWidget, QHBoxLayout, QScrollBar, QWidget

from controller.cli.cli_context import CLIContext
from controller.file.user_data_storage import append_stored_line, read_stored_lines, write_stored_lines
from controller.network import NetworkManager
from view.misc.termqt import Terminal, TerminalIO
from view.misc.termqt.terminal_widget import CursorState

if TYPE_CHECKING:
    from PySide6.QtGui import QFocusEvent

    from model import BoardConfiguration


logger = getLogger(__name__)

_NEWLINE_CHAR = 13
_BACKSPACE_CHAR = 8
_CANCEL_CHAR = 3
_ESCAPE_CHAR = 27
_ESC_UP_CHAR = 65
_ESC_DOWN_CHAR = 66
_ESC_RIGHT_CHAR = 67
_ESC_LEFT_CHAR = 68
_ESC_SEQUENCE_CHAR = 91
_ESC_CSI_PARAMETER_MIN_CHAR = 0x20
_ESC_CSI_PARAMETER_MAX_CHAR = 0x3F
_ESC_CSI_FINAL_MIN_CHAR = 0x40
_ESC_CSI_FINAL_MAX_CHAR = 0x7E


_HISTORY_STORAGE_FILE_NAME = "cli_history.list"
_HISTORY_MAX_ENTRIES = 10000
_TERMINAL_CLEAR_SPAN: Final = 200


class _EscapeSequenceState(Enum):
    """Parser state for ANSI escape sequences in the terminal input.

    The state is kept between write() calls because a single escape sequence may be split across multiple of them.
    """

    NONE = 0
    ESCAPE = 1
    CSI = 2


class _CommandHistory:
    """Process wide shared CLI command history persisted in the user data storage."""

    def __init__(self) -> None:
        """Initialize the history as not yet loaded from disk."""
        self._entries: list[str] = []
        self._loaded = False
        self._persistence_enabled = True
        self._appends_since_trim = 0

    def entries(self) -> list[str]:
        """Return the shared history entries, loading them from disk on first use."""
        if not self._loaded:
            self._loaded = True
            try:
                self._entries = read_stored_lines(_HISTORY_STORAGE_FILE_NAME)
            except OSError as e:
                self._persistence_enabled = False
                logger.warning("Unable to read the CLI command history. It will be kept in memory only: %s", e)
            else:
                atexit.register(self.save)
        return self._entries

    def __len__(self) -> int:
        """Return the number of shared history entries."""
        return len(self.entries())

    def __getitem__(self, index: int) -> str:
        """Return the shared history entry at the given index.

        Negative indexes count from the most recent entry backwards, matching the behaviour of a plain list.

        Args:
            index: the index of the entry to return

        Raises:
            IndexError: if the given index is out of bounds

        """
        return self.entries()[index]

    def append(self, command: str) -> None:
        """Append a command to the shared history and persist it.

        Empty commands and consecutive duplicates of the last entry are ignored.

        Args:
            command: the command to append

        """
        entries = self.entries()
        if not command or (entries and entries[-1] == command):
            return
        entries.append(command)
        if len(entries) > _HISTORY_MAX_ENTRIES:
            del entries[: len(entries) - _HISTORY_MAX_ENTRIES]
        self._appends_since_trim += 1
        if self._appends_since_trim >= _HISTORY_MAX_ENTRIES:
            self._appends_since_trim = 0
            self.save()
        self._persist_append(command)

    def _persist_append(self, command: str) -> None:
        """Append a command to the persisted history file.

        Persistence is disabled once appending fails: repeatedly logging write errors for every executed command
        would spam the log of an otherwise fully usable editor.

        Args:
            command: the command to append

        """
        if not self._persistence_enabled:
            return
        try:
            append_stored_line(_HISTORY_STORAGE_FILE_NAME, command)
        except OSError as e:
            self._persistence_enabled = False
            logger.warning("Unable to save the CLI command history. It will be kept in memory only: %s", e)

    def save(self) -> None:
        """Trim the persisted history file down to the most recent entries."""
        if not self._persistence_enabled:
            return
        try:
            stored = read_stored_lines(_HISTORY_STORAGE_FILE_NAME)
            if len(stored) > _HISTORY_MAX_ENTRIES:
                write_stored_lines(_HISTORY_STORAGE_FILE_NAME, stored[-_HISTORY_MAX_ENTRIES:])
        except OSError as e:
            logger.warning("Unable to save the CLI command history: %s", e)


_command_history = _CommandHistory()


class CLITerminalIO(TerminalIO):
    """Terminal IO implementation to adapter CLIContext."""

    def __init__(self, show: BoardConfiguration, terminal: Terminal, clear_span: int) -> None:
        """Initialize the IO adapter."""
        self._clear_span = clear_span
        self._context = CLIContext(show=show, network_manager=NetworkManager())
        self._stdout_callback = terminal.stdout
        self._buffer: list[int] = []
        self._history: _CommandHistory = _command_history
        self._history_cursor = 0
        self._history_cmd_stash = ""
        self._escape_state = _EscapeSequenceState.NONE
        self._cursor_in_buffer = 0
        self._displayed_line_length = 0
        terminal.stdin_callback = self.write
        terminal.resize_callback = self.resize
        self.spawn()

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
        input_line_changed = False
        # TODO implement tab completion here
        for b in buffer:
            if b == _NEWLINE_CHAR:
                cmd = bytes(self._buffer).decode(errors="ignore").strip()
                self._buffer.clear()
                _command_history.append(cmd)
                execution_successful = self._context.exec_command(cmd)
                self._stdout_callback(b"\n")
                self._stdout_callback(self._context.fetch_print_buffer().encode())
                executed_command = True
                self._history_cursor = 0
                self._history_cmd_stash = ""
                self._escape_state = _EscapeSequenceState.NONE
                self._cursor_in_buffer = 0
                self._displayed_line_length = 0
                input_line_changed = False
            elif b == _BACKSPACE_CHAR:
                self._escape_state = _EscapeSequenceState.NONE
                if self._remove_char_before_cursor():
                    input_line_changed = True
            elif b == _CANCEL_CHAR:
                self._escape_state = _EscapeSequenceState.NONE
                self._buffer.clear()
                self._cursor_in_buffer = 0
                self._history_cursor = 0
                self._history_cmd_stash = ""
                self._stdout_callback(b"^C\r\n> ")
                self._displayed_line_length = 0
                input_line_changed = False
            elif b == _ESCAPE_CHAR:
                self._escape_state = _EscapeSequenceState.ESCAPE
            elif self._escape_state == _EscapeSequenceState.ESCAPE:
                if b == _ESC_SEQUENCE_CHAR:
                    self._escape_state = _EscapeSequenceState.CSI
                elif b >= 32:
                    self._escape_state = _EscapeSequenceState.NONE
                    self._insert_byte(b)
                    input_line_changed = True
                else:
                    # an unexpected control byte terminates the partial escape sequence as well
                    self._escape_state = _EscapeSequenceState.NONE
            elif self._escape_state == _EscapeSequenceState.CSI:
                if _ESC_CSI_PARAMETER_MIN_CHAR <= b <= _ESC_CSI_PARAMETER_MAX_CHAR:
                    continue
                if _ESC_CSI_FINAL_MIN_CHAR <= b <= _ESC_CSI_FINAL_MAX_CHAR:
                    self._escape_state = _EscapeSequenceState.NONE
                    if b == _ESC_UP_CHAR:
                        self._history_previous_pressed()
                        input_line_changed = False
                    elif b == _ESC_DOWN_CHAR:
                        self._history_next_pressed()
                        input_line_changed = False
                    elif b == _ESC_LEFT_CHAR:
                        self._cursor_left_pressed()
                    elif b == _ESC_RIGHT_CHAR:
                        self._cursor_right_pressed()
                else:
                    self._escape_state = _EscapeSequenceState.NONE
            elif b < 32:
                continue
            else:
                self._insert_byte(b)
                input_line_changed = True
        if input_line_changed:
            self._redraw_input_line()
        if executed_command:
            if execution_successful:
                self._stdout_callback(b"\r\n> ")
            else:
                self._stdout_callback(b"\r\n[ERR] > ")

    def _history_previous_pressed(self) -> None:
        """Replace the input line with the previous (older) history entry, if one exists.

        The current input line is stashed away so that it can be restored when navigating back down to the newest
        entry. Nothing happens if there is no older entry available.
        """
        if len(self._history) < (self._history_cursor + 1):
            return
        if self._history_cursor == 0:
            self._history_cmd_stash = bytes(self._buffer).decode(errors="ignore")
        self._history_cursor += 1
        next_cmd_bytes = self._history[-1 * self._history_cursor].encode()
        self._buffer.clear()
        self._buffer.extend(next_cmd_bytes)
        self._cursor_in_buffer = 0
        self._redraw_input_line()

    def _history_next_pressed(self) -> None:
        """Replace the input line with the next (newer) history entry, if one exists.

        Navigating back below the newest entry restores the input line stashed when the history navigation was
        started. Nothing happens if the history navigation was not started yet.
        """
        if self._history_cursor == 0:
            return
        self._history_cursor -= 1
        next_cmd = self._history_cmd_stash if self._history_cursor == 0 else self._history[-1 * self._history_cursor]
        next_cmd_bytes = next_cmd.encode()
        self._buffer.clear()
        self._buffer.extend(next_cmd_bytes)
        self._cursor_in_buffer = 0
        self._redraw_input_line()

    def _cursor_left_pressed(self) -> None:
        """Move the input cursor one position to the left, if the start of the line is not reached yet."""
        if self._cursor_in_buffer == len(self._buffer):
            return
        self._cursor_in_buffer += 1
        self._stdout_callback(bytes([_ESCAPE_CHAR, _ESC_SEQUENCE_CHAR, _ESC_LEFT_CHAR]))

    def _cursor_right_pressed(self) -> None:
        """Move the input cursor one position to the right, if the end of the line is not reached yet."""
        if self._cursor_in_buffer == 0:
            return
        self._cursor_in_buffer -= 1
        self._stdout_callback(bytes([_ESCAPE_CHAR, _ESC_SEQUENCE_CHAR, _ESC_RIGHT_CHAR]))

    def _insert_byte(self, b: int) -> None:
        """Insert a printable input byte at the cursor position.

        Args:
            b: the byte to insert

        """
        self._buffer.insert(len(self._buffer) - self._cursor_in_buffer, b)

    def _remove_char_before_cursor(self) -> bool:
        """Remove the character in front of the cursor.

        Returns:
            whether a character has been removed

        """
        if len(self._buffer) <= self._cursor_in_buffer:
            return False
        del self._buffer[len(self._buffer) - self._cursor_in_buffer - 1]
        return True

    def _redraw_input_line(self) -> None:
        """Redraw the prompt and the complete input line and reposition the terminal cursor."""
        self._stdout_callback(b"\r> ")
        self._stdout_callback(bytes(self._buffer))
        overflow = self._displayed_line_length - len(self._buffer)
        if overflow > 0:
            self._stdout_callback(bytes([ord(" ")] * overflow))
        cursor_moves = self._cursor_in_buffer + max(overflow, 0)
        if cursor_moves > 0:
            self._stdout_callback(bytes([_ESCAPE_CHAR, _ESC_SEQUENCE_CHAR, _ESC_LEFT_CHAR]) * cursor_moves)
        self._displayed_line_length = len(self._buffer)

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
        self._io = CLITerminalIO(show, self._terminal_widget, _TERMINAL_CLEAR_SPAN)
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
