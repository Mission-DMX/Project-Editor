"""Contains UI Widget for control of event scheduler."""

from __future__ import annotations

from logging import getLogger
from queue import Queue
from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from model import FilterUpdateCallbackMixin, UIWidget
from view.show_mode.editor.editor_tab_widgets.ui_widget_editor._widget_holder import UIWidgetHolder
from view.show_mode.editor.node_editor_widgets.event_scheduler_config_widget.trigger_matrix_editor import (
    TriggerMatrixEditor,
)
from view.utility_widgets.jogwheel_spinbox import JogwheelSpinBox

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog

    import proto.FilterMode_pb2
    from model import UIPage

logger = getLogger(__name__)


class EventSchedulerCtrlUIWidget(FilterUpdateCallbackMixin, UIWidget):
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
        self._callback_registered: bool = False
        self._latest_player_widget: QWidget | None = None
        self._latest_config_widget: QWidget | None = None
        if not self.configuration.get("width"):
            self.configuration["width"] = "800"
        if not self.configuration.get("height"):
            self.configuration["height"] = "600"

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        outstanding_updates_list = []
        while not self._operations_queue.empty():
            item = self._operations_queue.get(block=False)
            outstanding_updates_list.append(item)
        return outstanding_updates_list

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        self._register_fish_callback(self.parent.scene.get_filter_by_id(self.filter_ids[0]))
        self._latest_player_widget = self._generate_widget(True, parent)
        return self._latest_player_widget

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        self._latest_config_widget = self._generate_widget(False, parent)
        return self._latest_config_widget

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        uiw = EventSchedulerCtrlUIWidget(new_parent, self.configuration.copy())
        self.copy_base(uiw)
        return uiw

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        w = QWidget()
        w.setMinimumWidth(300)
        w.setMinimumHeight(100)
        form_layout = QFormLayout()
        width_box = JogwheelSpinBox()
        width_box.setMinimum(200)
        width_box.setMaximum(16384)
        width_box.setValue(int(self.configuration.get("width") or "800"))
        width_box.valueChanged.connect(self._config_width_value_changed)
        form_layout.addRow("Width", width_box)
        height_box = JogwheelSpinBox()
        height_box.setMinimum(150)
        height_box.setMaximum(16384)
        height_box.setValue(int(self.configuration.get("height") or "600"))
        height_box.valueChanged.connect(self._config_height_value_changed)
        form_layout.addRow("Height", height_box)
        # TODO add controls for enabling/disabling the scheduler advancement and for overriding the sync event
        w.setLayout(form_layout)
        return w

    def _generate_widget(self, used_in_player: bool, parent: QWidget | None) -> QWidget:
        w = QWidget(parent=parent)
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("Step: "))
        override_step_spinbox = JogwheelSpinBox()
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

            associated_filter = self.parent.scene.get_filter_by_id(self.filter_ids[0])
            matrix_editor.number_of_steps = int(associated_filter.initial_parameters.get("length", "0"))
            event_data = associated_filter.filter_configurations.get("event_data", "").split(";")
            event_names = associated_filter.filter_configurations.get("event_names", "").split(";")
            for ed, e_name in zip(event_data, event_names, strict=True):
                if len(ed) < 1:
                    continue
                matrix_editor.add_event(ed, e_name)
            matrix_editor.active_event_data = associated_filter.initial_parameters.get("update_triggers", "")
            matrix_editor.highlight_current_step = True
        w.setEnabled(used_in_player)
        width = max(int(self.configuration.get("width") or "800"), w.minimumSizeHint().width())
        height = max(int(self.configuration.get("height") or "600"), w.minimumSizeHint().height())
        w.setFixedWidth(width)
        w.setFixedHeight(height)
        w.setMinimumSize(width, height)
        self.size = (width, height)
        return w

    def _config_width_value_changed(self, new_value: int) -> None:
        self.size = (new_value, self.size[1])
        for widget in [self._latest_player_widget, self._latest_config_widget]:
            if widget is not None:
                widget.setFixedWidth(new_value)
                wh = widget.parent()
                if isinstance(wh, UIWidgetHolder):
                    wh.update_size()
        self.configuration["width"] = str(new_value)

    def _config_height_value_changed(self, new_value: int) -> None:
        self.size = (self.size[0], new_value)
        for widget in [self._latest_player_widget, self._latest_config_widget]:
            if widget is not None:
                widget.setFixedHeight(new_value)
                wh = widget.parent()
                if isinstance(wh, UIWidgetHolder):
                    wh.update_size()
        self.configuration["height"] = str(new_value)

    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        if self._active_matrix_editor is None:
            return
        if param.parameter_key != "step":
            return
        self._active_matrix_editor.current_step = int(param.parameter_value)

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
