"""Contains Trigger Matrix Editor"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

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
        self._highlight_current_steps: bool = False
        self._maximum_steps: int = 0
        self._current_step: int = 0
        self._events: list[str] = []

    # TODO implement all methods