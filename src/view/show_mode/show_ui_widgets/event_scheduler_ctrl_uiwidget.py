"""Contains UI Widget for control of event scheduler."""

from __future__ import annotations

from logging import getLogger
from queue import Queue
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
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
    from model import Filter, UIPage

logger = getLogger(__name__)


def _to_int(value: str, default: int) -> int:
    """Parse an integer configuration value, falling back to a default for malformed input."""
    try:
        return int(value)
    except ValueError:
        logger.warning("Malformed integer value %r, falling back to %d.", value, default)
        return default


class _EventSchedulerWidget(QWidget):
    """Inner widget of the event scheduler control.

    The widget holder derives the holder size from this widget's size hints. A plain QWidget with a layout reports
    hints computed from its layout contents, which are independent of the configured (fixed) widget size -- for this
    widget they are dominated by the embedded scroll area and therefore small. Overriding the hints to report the
    configured size keeps the holder sizing in sync with the configuration.
    """

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent)
        self._configured_size = QSize(800, 600)

    def set_configured_size(self, width: int, height: int) -> None:
        """Update the size this widget reports to its holder and parent layout."""
        if width < 1 or height < 1:
            return
        if self._configured_size == QSize(width, height):
            return
        self._configured_size = QSize(width, height)
        self.updateGeometry()

    @override
    def sizeHint(self) -> QSize:
        return QSize(self._configured_size)

    @override
    def minimumSizeHint(self) -> QSize:
        return QSize(self._configured_size)


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
        self._step_spinbox: JogwheelSpinBox | None = None
        self._operations_queue: Queue[tuple[str, str]] = Queue()
        self._latest_player_widget: _EventSchedulerWidget | None = None
        self._latest_config_widget: _EventSchedulerWidget | None = None
        if not self.configuration.get("width"):
            self.configuration["width"] = "800"
        if not self.configuration.get("height"):
            self.configuration["height"] = "600"
        self.size = (int(self.configuration["width"]), int(self.configuration["height"]))

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        outstanding_updates_list = []
        while not self._operations_queue.empty():
            item = self._operations_queue.get(block=False)
            outstanding_updates_list.append(item)
        return outstanding_updates_list

    @override
    def set_filter(self, f: Filter, i: int) -> None:
        """Link the widget to an event scheduler filter and start listening to its fish updates."""
        if not f:
            return
        super().set_filter(f, i)
        self._register_fish_callback(f)

    @override
    def notify_id_rename(self, old_id: str, new_id: str) -> None:
        """Move the linked filter id and the fish callback along when the filter is renamed."""
        super().notify_id_rename(old_id, new_id)
        self._handle_filter_id_rename(old_id, new_id)

    def _get_linked_filter(self) -> Filter | None:
        """Return the linked event scheduler filter if it is set and resolvable."""
        filter_ids = self.filter_ids
        if not filter_ids:
            return None
        return self.parent.scene.get_filter_by_id(filter_ids[0])

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        associated_filter = self._get_linked_filter()
        if associated_filter is None:
            logger.warning("No resolvable event scheduler filter linked; fish updates stay disabled.")
        else:
            self._register_fish_callback(associated_filter)
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
        width_box = QSpinBox()
        width_box.setMinimum(200)
        width_box.setMaximum(16384)
        width_box.setValue(int(self.configuration.get("width") or "800"))
        width_box.valueChanged.connect(self._config_width_value_changed)
        form_layout.addRow("Width", width_box)
        height_box = QSpinBox()
        height_box.setMinimum(150)
        height_box.setMaximum(16384)
        height_box.setValue(int(self.configuration.get("height") or "600"))
        height_box.valueChanged.connect(self._config_height_value_changed)
        form_layout.addRow("Height", height_box)
        # TODO add controls for enabling/disabling the scheduler advancement and for overriding the sync event
        w.setLayout(form_layout)
        return w

    def _generate_widget(self, used_in_player: bool, parent: QWidget | None) -> QWidget:
        w = _EventSchedulerWidget(parent)
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("Step: "))
        override_step_spinbox = JogwheelSpinBox()
        override_step_spinbox.setMinimum(0)
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
            self._step_spinbox = override_step_spinbox

            associated_filter = self._get_linked_filter()
            if associated_filter is None:
                logger.warning("No resolvable event scheduler filter linked; the player widget stays empty.")
                override_step_spinbox.setMaximum(0)
            else:
                number_of_steps = _to_int(associated_filter.initial_parameters.get("length", "0"), 0)
                matrix_editor.number_of_steps = number_of_steps
                event_data = associated_filter.filter_configurations.get("event_data", "").split(";")
                event_names = associated_filter.filter_configurations.get("event_names", "").split(";")
                while len(event_names) < len(event_data):
                    event_names.append("No Name")
                for ed, e_name in zip(event_data, event_names, strict=False):
                    if len(ed) < 1:
                        continue
                    matrix_editor.add_event(ed, e_name)
                matrix_editor.active_event_data = associated_filter.initial_parameters.get("update_triggers", "")
                matrix_editor.current_step = _to_int(associated_filter.initial_parameters.get("step", "0"), 0)
                # The spin box mirrors the step range and current step of the linked filter. Connecting it after
                # setting the initial value avoids pushing that value back to fish.
                override_step_spinbox.setMaximum(max(number_of_steps - 1, 0))
                override_step_spinbox.setValue(matrix_editor.current_step)
                override_step_spinbox.valueChanged.connect(self._received_new_step)
                matrix_editor.highlight_current_step = True
        w.setEnabled(used_in_player)
        configured_width = int(self.configuration.get("width") or "800")
        configured_height = int(self.configuration.get("height") or "600")
        w.set_configured_size(configured_width, configured_height)
        w.setFixedSize(configured_width, configured_height)
        return w

    def _config_width_value_changed(self, new_value: int) -> None:
        self.configuration["width"] = str(new_value)
        self._apply_configured_size()

    def _config_height_value_changed(self, new_value: int) -> None:
        self.configuration["height"] = str(new_value)
        self._apply_configured_size()

    def _apply_configured_size(self) -> None:
        """Push the configured size into the model, the generated widgets and their holders."""
        width = int(self.configuration.get("width") or "800")
        height = int(self.configuration.get("height") or "600")
        self.size = (width, height)
        for widget in [self._latest_player_widget, self._latest_config_widget]:
            if widget is None:
                continue
            widget.set_configured_size(width, height)
            widget.setFixedWidth(width)
            widget.setFixedHeight(height)
            wh = widget.parent()
            if isinstance(wh, UIWidgetHolder):
                wh.update_size()

    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        if self._active_matrix_editor is None:
            return
        if param.parameter_key != "step":
            return
        matrix_editor = self._active_matrix_editor
        matrix_editor.current_step = _to_int(param.parameter_value, matrix_editor.current_step)
        spinbox = self._step_spinbox
        if spinbox is not None:
            spinbox.blockSignals(True)
            spinbox.setValue(matrix_editor.current_step)
            spinbox.blockSignals(False)

    def _decrease_clicked(self, _: bool) -> None:
        if self._active_matrix_editor is None:
            return
        if self._active_matrix_editor.number_of_steps < 1:
            return
        self._active_matrix_editor.number_of_steps -= 1
        self._update_step_spinbox_bounds(self._active_matrix_editor.number_of_steps)
        self._operations_queue.put(("length", str(self._active_matrix_editor.number_of_steps)))
        self.push_update()

    def _increase_clicked(self, _: bool) -> None:
        if self._active_matrix_editor is None:
            return
        self._active_matrix_editor.number_of_steps += 1
        self._update_step_spinbox_bounds(self._active_matrix_editor.number_of_steps)
        self._operations_queue.put(("length", str(self._active_matrix_editor.number_of_steps)))
        self.push_update()

    def _update_step_spinbox_bounds(self, number_of_steps: int) -> None:
        """Keep the step spin box range in sync with the number of steps of the linked filter."""
        spinbox = self._step_spinbox
        if spinbox is None:
            return
        spinbox.setMaximum(max(number_of_steps - 1, 0))

    def _received_new_step(self, new_default_step: int) -> None:
        self._operations_queue.put(("step", str(new_default_step)))
        self.push_update()

    def _event_state_updated(self, step: int, event_idx: int, new_state: bool) -> None:
        self._operations_queue.put(("update_triggers", f"{step},{event_idx},{'TRUE' if new_state else 'FALSE'}"))
        self.push_update()
