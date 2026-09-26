"""Contains UI Widget for control of event scheduler."""

from __future__ import annotations

from logging import getLogger
from queue import Queue
from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget

from model import UIWidget
from view.show_mode.editor.node_editor_widgets.event_scheduler_config_widget.trigger_matrix_editor import (
    TriggerMatrixEditor,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog

    from model import UIPage

logger = getLogger(__name__)


class EventSchedulerCtrlUIWidget(UIWidget):
    """Event scheduler control widget.

    This widget allows the user to override the event scheduler parameters live.
    It provides a matrix editor for triggers, buttons to control the number of steps, and a spin box to override the
    current step.

    In the future, a mechanism to enable/disaable the advancement es well as a method to override the synchronization
    event might be added.

    """

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize the UI widget."""
        super().__init__(parent, configuration)
        self._active_matrix_editor: TriggerMatrixEditor | None = None
        self._operations_queue: Queue[tuple[str, str]] = Queue()

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        outstanding_updates_list = []
        while not self._operations_queue.empty():
            item = self._operations_queue.get(block=False)
            outstanding_updates_list.append(item)
        return outstanding_updates_list

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        return self._generate_widget(True)

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        return self._generate_widget(False)

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        uiw = EventSchedulerCtrlUIWidget(new_parent, self.configuration.copy())
        self.copy_base(uiw)
        return uiw

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        pass  # TODO

    def _generate_widget(self, used_in_player: bool) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("Step: "))
        override_step_spinbox = QSpinBox()  # FIXME use JogwheelSpinBox once PR #416 got merged.
        override_step_spinbox.setMinimum(1)
        button_layout.addWidget(override_step_spinbox)
        button_layout.addStretch()
        decrease_steps_button = QPushButton("-")
        button_layout.addWidget(decrease_steps_button)
        increase_steps_button = QPushButton("+")
        button_layout.addWidget(increase_steps_button)
        layout.addLayout(button_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        matrix_editor = TriggerMatrixEditor()
        scroll_area.setWidget(matrix_editor)
        layout.addWidget(scroll_area)
        w.setLayout(layout)
        if used_in_player:
            if self._active_matrix_editor is not None:
                logger.error("The matrix editor widget is already populated.")
            self._active_matrix_editor = matrix_editor
            matrix_editor.event_updated.connect(self._event_state_updated)
            decrease_steps_button.clicked.connect(self._decrease_clicked)
            increase_steps_button.clicked.connect(self._increase_clicked)
            override_step_spinbox.valueChanged.connect(self._received_new_step)
        # TODO load filter settings
        w.setEnabled(used_in_player)
        # TODO set fixed size based on widget settings
        return w

    def _decrease_clicked(self, _: bool) -> None:
        if self._active_matrix_editor is None:
            return
        if self._active_matrix_editor.number_of_steps < 1:
            return
        self._active_matrix_editor.number_of_steps -= 1
        self._operations_queue.put(("length", str(self._active_matrix_editor.number_of_steps)))
        self.push_update()

    def _increase_clicked(self, _: bool) -> None:
        if self._active_matrix_editor is None:
            return
        self._active_matrix_editor.number_of_steps += 1
        self._operations_queue.put(("length", str(self._active_matrix_editor.number_of_steps)))
        self.push_update()

    def _received_new_step(self, new_default_step: int) -> None:
        self._operations_queue.put(("step", str(new_default_step)))
        self.push_update()

    def _event_state_updated(self, step: int, event_idx: int, new_state: bool) -> None:
        self._operations_queue.put(("update_triggers", f"{step},{event_idx},{"TRUE" if new_state else "FALSE"}"))
        self.push_update()
