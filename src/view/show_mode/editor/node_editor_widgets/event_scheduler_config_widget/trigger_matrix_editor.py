"""Contains Trigger Matrix Editor"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QMouseEvent, QPaintEvent
from PySide6.QtCore import Qt, Signal, QRect
import numpy as np

class TriggerMatrixEditor(QWidget):
    """Class providing user with option to select when which events should be triggered.

    The widget uses a custom renderer and only updates the required parts.

    Usage:
    0. (Call clear() if required)
    1. Call add_event for every output event
    2. set the number_of_steps property to the desired number of steps.
    3. Load data using the event_data property.

    Signals:
    - event_updated(step: int, event-index: int, new-state: bool)

    Properties:
    - highlight_current_step: bool -- should the current step the filter is in be highlighted?
    - current_step: int -- get or set the current step (0 to highlight_current_step)
    - event_data: str -- get or set all event cells. See https://mission-dmx.org/docs/Filters/Filter_Types/misc.html for the format.

    """


    def __init__(self, parent: QWidget) -> None:
        """Initialize the widget"""
        super().__init__(parent)
        self._highlight_current_step: bool = False
        self._number_of_steps: int = 0
        self._current_step: int = 0
        self._events: list[str] = []
        self._states: np.ndarray = np.zeros((0, 0), dtype=bool)

        # Layout constants
        self._header_height: int = 30
        self._event_name_width: int = 150
        self._cell_width: int = 40
        self._cell_height: int = 30

        # Colors
        self._color_enabled = QColor(0, 255, 0)  # Green
        self._color_disabled = QColor(255, 0, 0)  # Red
        self._color_header_highlight = QColor(100, 149, 237)  # Cornflower blue
        self._color_header_normal = QColor(200, 200, 200)  # Light gray
        self._color_text = QColor(0, 0, 0)  # Black
        self._color_grid = QColor(150, 150, 150)  # Gray

        # Enable mouse tracking for better interaction
        self.setMouseTracking(False)
        self.setFocusPolicy(Qt.StrongFocus)

    def clear(self) -> None:
        """Clear all events and reset the matrix"""
        self._events = []
        self._number_of_steps = 0
        self._current_step = 0
        self._states = np.zeros((0, 0), dtype=bool)
        self.update()

    def add_event(self, event_name: str) -> None:
        """Add a new event to the matrix"""
        self._events.append(event_name)
        self._resize_states()
        self.update()

    def _resize_states(self) -> None:
        """Resize the states array to match current events and steps"""
        num_events = len(self._events)
        new_states = np.zeros((num_events, self._number_of_steps), dtype=bool)

        if self._states.size > 0:
            min_events = min(num_events, self._states.shape[0])
            min_steps = min(self._number_of_steps, self._states.shape[1])
            new_states[:min_events, :min_steps] = self._states[:min_events, :min_steps]

        self._states = new_states

    @property
    def highlight_current_step(self) -> bool:
        """Get whether current step should be highlighted"""
        return self._highlight_current_step

    @highlight_current_step.setter
    def highlight_current_step(self, value: bool) -> None:
        """Set whether current step should be highlighted"""
        if self._highlight_current_step != value:
            self._highlight_current_step = value
            self.update()

    @property
    def current_step(self) -> int:
        """Get the current step"""
        return self._current_step

    @current_step.setter
    def current_step(self, value: int) -> None:
        """Set the current step"""
        if self._current_step != value:
            self._current_step = max(0, min(value, self._number_of_steps - 1)) if self._number_of_steps > 0 else 0
            if self._highlight_current_step:
                # FIXME only update the affected regions
                self.update()

    @property
    def number_of_steps(self) -> int:
        """Get the number of steps"""
        return self._number_of_steps

    @number_of_steps.setter
    def number_of_steps(self, value: int) -> None:
        """Set the number of steps"""
        if self._number_of_steps != value:
            self._number_of_steps = max(0, value)
            self._resize_states()
            self.update()

    @property
    def event_data(self) -> str:
        """Get the event data as a string."""
        if self._number_of_steps == 0 or len(self._events) == 0:
            return ""

        steps_data = []
        for step in range(self._number_of_steps):
            for event in range(len(self._events)):
                if self._states[event, step]:
                    steps_data.append(f"{step},{event},TRUE")

        return ";".join(steps_data)

    @event_data.setter
    def event_data(self, value: str) -> None:
        """Set the event data from a string.

        Format: For each step, comma-separated event indices that are enabled.
        Steps are separated by semicolons.
        """
        if not value:
            if self._states.size > 0:
                self._states.fill(False)
            self.update()
            return

        # Reset all states first
        if self._states.size > 0:
            self._states.fill(False)

        for entry in value.split(';'):
            step, event, state = entry.split(',')
            self._states[int(event), int(step)] = state.lower() == "true"

        self.update()

    def _get_cell_rect(self, event_idx: int, step: int) -> QRect:
        """Get the rectangle for a specific cell"""
        x = self._event_name_width + step * self._cell_width
        y = self._header_height + event_idx * self._cell_height
        return QRect(x, y, self._cell_width, self._cell_height)

    def _get_step_rect(self, step: int) -> QRect:
        """Get the rectangle for a step header"""
        x = self._event_name_width + step * self._cell_width
        y = 0
        return QRect(x, y, self._cell_width, self._header_height)

    def _get_event_rect(self, event_idx: int) -> QRect:
        """Get the rectangle for an event name"""
        x = 0
        y = self._header_height + event_idx * self._cell_height
        return QRect(x, y, self._event_name_width, self._cell_height)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Custom paint event for efficient rendering"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        update_rect = event.rect()

        # Draw headers (steps)
        for step in range(self._number_of_steps):
            header_rect = self._get_step_rect(step)

            if update_rect.intersects(header_rect):
                if self._highlight_current_step and step == self._current_step:
                    painter.fillRect(header_rect, self._color_header_highlight)
                else:
                    painter.fillRect(header_rect, self._color_header_normal)

                painter.setPen(self._color_grid)
                painter.drawRect(header_rect)

                painter.setPen(self._color_text)
                painter.drawText(header_rect, Qt.AlignCenter, str(step))

        # Draw event names
        for event_idx, event_name in enumerate(self._events):
            event_rect = self._get_event_rect(event_idx)

            if update_rect.intersects(event_rect):
                painter.fillRect(event_rect, self._color_header_normal)
                painter.setPen(self._color_grid)
                painter.drawRect(event_rect)
                painter.setPen(self._color_text)
                painter.drawText(event_rect, Qt.AlignCenter, event_name)

        # Draw cells
        for event_idx in range(len(self._events)):
            for step in range(self._number_of_steps):
                cell_rect = self._get_cell_rect(event_idx, step)

                if update_rect.intersects(cell_rect):
                    if self._states[event_idx, step]:
                        painter.fillRect(cell_rect, self._color_enabled)
                    else:
                        painter.fillRect(cell_rect, self._color_disabled)

                    painter.setPen(self._color_grid)
                    painter.drawRect(cell_rect)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click to toggle cell state"""
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.pos()
        x, y = pos.x(), pos.y()

        # Check if click is in the cell area (not headers or event names)
        if x < self._event_name_width or y < self._header_height:
            super().mousePressEvent(event)
            return

        # Calculate which cell was clicked
        step = (x - self._event_name_width) // self._cell_width
        event_idx = (y - self._header_height) // self._cell_height

        # Validate indices
        if 0 <= step < self._number_of_steps and 0 <= event_idx < len(self._events):
            # Toggle state
            new_state = not self._states[event_idx, step]
            self._states[event_idx, step] = new_state

            # Emit signal
            self.event_updated.emit(step, event_idx, new_state)

            # Update only the clicked cell
            cell_rect = self._get_cell_rect(event_idx, step)
            self.update(cell_rect)

    def sizeHint(self):
        """Suggest a reasonable size for the widget"""
        width = self._event_name_width + self._number_of_steps * self._cell_width
        height = self._header_height + len(self._events) * self._cell_height
        return (width, height)

    def minimumSizeHint(self):
        """Minimum size hint"""
        return (self._event_name_width + 5 * self._cell_width,
                self._header_height + 3 * self._cell_height)