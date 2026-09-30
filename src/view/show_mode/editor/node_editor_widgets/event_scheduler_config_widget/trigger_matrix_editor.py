"""Contains Trigger Matrix Editor."""

from __future__ import annotations

from logging import getLogger
from typing import override

import numpy as np
from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from model.events import parse_update_trigger_entries

logger = getLogger(__name__)


class TriggerMatrixEditor(QWidget):
    """Class providing user with option to select when which events should be triggered.

    The widget uses a custom renderer and only updates the required parts.

    Step indices in the API and in the serialized data are 0-based; the painted step header shows 1-based step
    numbers for readability.

    Usage:
    0. (Call clear() if required)
    1. Call add_event for every output event
    2. set the number_of_steps property to the desired number of steps.
    3. Load data using the event_data property.

    Signals:
    - event_updated(step: int, event-index: int, new-state: bool)

    Properties:
    - highlight_current_step: bool -- should the current step the filter is in be highlighted?
    - current_step: int -- get or set the current step (0 to number_of_steps - 1)
    - event_data: str -- get or set all event cells. See https://mission-dmx.org/docs/Filters/Filter_Types/misc.html
      for the format.
    - event_names: list[str] -- Associated names of the events

    """

    event_updated = Signal(int, int, bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the widget."""
        super().__init__(parent)
        self._highlight_current_step: bool = False
        self._number_of_steps: int = 0
        self._current_step: int = 0
        self._events: list[str] = []
        self._event_names: list[str] = []
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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def clear(self) -> None:
        """Clear all events and reset the matrix."""
        self._events.clear()
        self._event_names.clear()
        self._number_of_steps = 0
        self._current_step = 0
        self._states = np.zeros((0, 0), dtype=bool)
        self._notify_size_change()

    def add_event(self, event_description: str, event_name: str) -> None:
        """Add a new event to the matrix."""
        self._events.append(event_description)
        self._event_names.append(event_name)
        self._resize_states()
        self._notify_size_change()

    def remove_event(self, event_idx: int) -> None:
        """Remove the event with the given index from the matrix.

        The trigger states of the remaining events are preserved and keep their association with their event.
        """
        if not 0 <= event_idx < len(self._events):
            logger.warning("Cannot remove non-existing event with index %d.", event_idx)
            return
        del self._events[event_idx]
        del self._event_names[event_idx]
        if event_idx < self._states.shape[0]:
            self._states = np.delete(self._states, event_idx, axis=0)
        self._notify_size_change()

    def update_event(self, event_idx: int, event_description: str) -> None:
        """Update the stored description of an existing event without touching its trigger states."""
        if not 0 <= event_idx < len(self._events):
            logger.warning("Cannot update non-existing event with index %d.", event_idx)
            return
        self._events[event_idx] = event_description

    def apply_event_state(self, step: int, event_idx: int, state: bool) -> None:
        """Set the state of a single cell without emitting the event_updated signal.

        Args:
            step: The 0-based step index of the cell to update.
            event_idx: The index of the event whose cell should be updated.
            state: The new trigger state of the cell.

        """
        if not (0 <= event_idx < len(self._events) and 0 <= step < self._number_of_steps):
            logger.warning(
                "Cannot apply the state of non-existing cell (event %d, step %d; %d events, %d steps).",
                event_idx,
                step,
                len(self._events),
                self._number_of_steps,
            )
            return
        if self._states[event_idx, step] == state:
            return
        self._states[event_idx, step] = state
        self.update(self._get_cell_rect(event_idx, step))

    def _resize_states(self) -> None:
        """Resize the states array to match current events and steps."""
        num_events = len(self._events)
        new_states = np.zeros((num_events, self._number_of_steps), dtype=bool)

        if self._states.size > 0:
            min_events = min(num_events, self._states.shape[0])
            min_steps = min(self._number_of_steps, self._states.shape[1])
            new_states[:min_events, :min_steps] = self._states[:min_events, :min_steps]

        self._states = new_states

    def _notify_size_change(self) -> None:
        """Invalidate layout caches and schedule a repaint after a size hint change."""
        self.updateGeometry()
        self.update()

    @property
    def highlight_current_step(self) -> bool:
        """Get whether current step should be highlighted."""
        return self._highlight_current_step

    @highlight_current_step.setter
    def highlight_current_step(self, value: bool) -> None:
        """Set whether current step should be highlighted."""
        if self._highlight_current_step != value:
            self._highlight_current_step = value
            self.update()

    @property
    def event_names(self) -> list[str]:
        """Get a copy of the event name list."""
        return list(self._event_names)

    @event_names.setter
    def event_names(self, value: list[str]) -> None:
        self._event_names = value
        self.update()

    @property
    def current_step(self) -> int:
        """Get the current step."""
        return self._current_step

    @current_step.setter
    def current_step(self, value: int) -> None:
        """Set the current step, clamping it into the valid step range."""
        if self._current_step != value:
            old_step = self._current_step
            self._current_step = self._clamped_step(value)
            if self._highlight_current_step:
                for step in {old_step, self._current_step}:
                    self.update(self._get_step_rect(step))

    @property
    def number_of_steps(self) -> int:
        """Get the number of steps."""
        return self._number_of_steps

    @number_of_steps.setter
    def number_of_steps(self, value: int) -> None:
        """Set the number of steps, keeping the current step inside the new range."""
        new_step_count = max(0, value)
        if self._number_of_steps == new_step_count:
            return
        self._number_of_steps = new_step_count
        self._resize_states()
        self._current_step = self._clamped_step(self._current_step)
        self._notify_size_change()

    def _clamped_step(self, step: int) -> int:
        """Clamp a step index into the range allowed by the current number of steps."""
        return max(0, min(step, self._number_of_steps - 1)) if self._number_of_steps > 0 else 0

    @property
    def active_event_data(self) -> str:
        """Get the event data as a string."""
        if self._number_of_steps == 0 or len(self._events) == 0:
            return ""

        steps_data: list[str] = []
        for step in range(self._number_of_steps):
            steps_data.extend(f"{step},{event},TRUE" for event in range(len(self._events)) if self._states[event, step])
        return ";".join(steps_data)

    @active_event_data.setter
    def active_event_data(self, value: str) -> None:
        """Set the event data from a string, replacing all previous states."""
        if not value:
            if self._states.size > 0:
                self._states.fill(False)
            self.update()
            return

        # Reset all states first
        if self._states.size > 0:
            self._states.fill(False)

        for step, event, state in parse_update_trigger_entries(value):
            if not (0 <= event < self._states.shape[0] and 0 <= step < self._states.shape[1]):
                logger.warning(
                    "Skipping out-of-range update trigger entry (event %d, step %d; %d events, %d steps).",
                    event,
                    step,
                    self._states.shape[0],
                    self._states.shape[1],
                )
                continue
            self._states[event, step] = state

        self.update()

    def _get_cell_rect(self, event_idx: int, step: int) -> QRect:
        """Get the rectangle for a specific cell."""
        x = self._event_name_width + step * self._cell_width
        y = self._header_height + event_idx * self._cell_height
        return QRect(x, y, self._cell_width, self._cell_height)

    def _get_step_rect(self, step: int) -> QRect:
        """Get the rectangle for a step header."""
        x = self._event_name_width + step * self._cell_width
        y = 0
        return QRect(x, y, self._cell_width, self._header_height)

    def _get_event_rect(self, event_idx: int) -> QRect:
        """Get the rectangle for an event name."""
        x = 0
        y = self._header_height + event_idx * self._cell_height
        return QRect(x, y, self._event_name_width, self._cell_height)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the matrix content, rendering only the parts that intersect the update region."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

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
                painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, str(step + 1))

        # Draw event names
        for event_idx, event_name in enumerate(self._event_names):
            event_rect = self._get_event_rect(event_idx)

            if update_rect.intersects(event_rect):
                painter.fillRect(event_rect, self._color_header_normal)
                painter.setPen(self._color_grid)
                painter.drawRect(event_rect)
                painter.setPen(self._color_text)
                painter.drawText(event_rect, Qt.AlignmentFlag.AlignCenter, event_name)

        # Draw cells
        for event_idx in range(len(self._event_names)):
            for step in range(self._number_of_steps):
                cell_rect = self._get_cell_rect(event_idx, step)

                if update_rect.intersects(cell_rect):
                    if self._states[event_idx, step]:
                        painter.fillRect(cell_rect, self._color_enabled)
                    else:
                        painter.fillRect(cell_rect, self._color_disabled)

                    painter.setPen(self._color_grid)
                    painter.drawRect(cell_rect)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click to toggle cell state."""
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint()
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

    @override
    def sizeHint(self) -> QSize:
        """Suggest a reasonable size for the widget."""
        width = self._event_name_width + self._number_of_steps * self._cell_width
        height = self._header_height + len(self._events) * self._cell_height
        return QSize(width, height)

    @override
    def minimumSizeHint(self) -> QSize:
        """Minimum size hint."""
        return QSize(self._event_name_width + 5 * self._cell_width, self._header_height + 3 * self._cell_height)
