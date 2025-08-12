"""Label for transitions."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from model.filter_data.utility import format_seconds

if TYPE_CHECKING:
    from model.filter_data.sequencer.transition import Transition


class TransitionLabel(QWidget):
    """The purpose of this class is to present the user with adequate information regarding a transition in the list."""

    def __init__(self, transition: Transition, position: int, parent: QWidget | None = None) -> None:
        """Transition label.

        Args:
            transition: The transition to represent.
            position: The id of the transition in the model.
            parent: The parent widget of this label.

        """
        super().__init__(parent)
        layout = QHBoxLayout()
        self._transition_id_label = QLabel(self)
        self._transition_id_label.setText(str(position))
        layout.addWidget(self._transition_id_label)
        layout.addSpacing(10)
        self._transition_name_label = QLabel(self)
        layout.addWidget(self._transition_name_label)
        self.setLayout(layout)
        layout.addStretch()
        self._event_label = QLabel(self)
        layout.addWidget(self._event_label)
        layout.addStretch()
        self._duration_label = QLabel(self)
        self._duration_label.setFixedWidth(100)
        layout.addWidget(self._duration_label)
        self.update_labels(transition)

    def update_labels(self, transition: Transition) -> None:
        """Update the label according to the provided transition."""
        self._transition_name_label.setText(transition.name)
        self._event_label.setText(str(transition._trigger_event))
        self._duration_label.setText(format_seconds(transition.duration))
