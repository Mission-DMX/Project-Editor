from collections import Counter
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from model.filter_data.utility import format_seconds

if TYPE_CHECKING:
    from model.filter_data.sequencer.transition import Transition


class TransitionLabel(QWidget):
    def __init__(self, transition: "Transition", position: int, parent=None):
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

    def update_labels(self, transition: "Transition"):
        self._transition_name_label.setText(transition.name)
        self._event_label.setText(str(transition._trigger_event))
        self._duration_label.setText(format_seconds(transition.duration))
