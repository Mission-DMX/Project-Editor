"""Provides configuration widget for Color2Colorwheel adapter."""

from __future__ import annotations

from typing import override, TYPE_CHECKING

from PySide6.QtWidgets import QWidget, QFormLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox, QListWidget, \
    QSpinBox, QSpacerItem, QSizePolicy, QListWidgetItem, QDialog, QDoubleSpinBox, QDialogButtonBox

from model import ColorHSI
from model.ofl.fixture import UsedFixture
from view.dialogs.selection_dialog import SelectionDialog
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.show_ui_widgets.debug_viz_widgets import ColorLabel
from model.virtual_filters.color_to_colorwheel import extract_colorwheel_mappings_from_fixture

if TYPE_CHECKING:
    from view.show_mode.editor.nodes import FilterNode
    from model.virtual_filters.color_to_colorwheel import ColorToColorWheel


class _ColorMappingListWidgetItem(QListWidgetItem):
    """Purpose of this widget is to display a single mapping."""

    def __init__(self, parent: QListWidget, color: ColorHSI, slot_value: int):
        """Initializes and adds the widget based on the provided color and slot value."""
        super().__init__()
        self.color = color
        self.slot_value = slot_value

        widget = QWidget()
        widget.setLayout(QHBoxLayout())
        self._color_label = ColorLabel()
        self._color_label.set_color(self.color)
        widget.layout().addWidget(self._color_label)
        self._slot_label = QLabel(str(slot_value))
        widget.layout().addWidget(self._slot_label)

        parent.addItem(self)
        parent.setItemWidget(self, widget)
        self.setSizeHint(widget.sizeHint())


class _ColorSlotInputDialog(QDialog):
    """Query a color and a slot."""

    def __init__(self, parent: QWidget, list_widget: QListWidget):
        """Initializes the dialog."""
        super().__init__(parent)

        self._list_widget = list_widget

        layout = QFormLayout()
        self._hue_tb = QDoubleSpinBox()
        self._hue_tb.setRange(0, 360)
        self._hue_tb.setDecimals(2)
        layout.addRow("Hue", self._hue_tb)
        self._saturation_tb = QDoubleSpinBox()
        self._saturation_tb.setDecimals(5)
        self._saturation_tb.setValue(1.0)
        self._saturation_tb.setRange(0, 1)
        layout.addRow("Saturation", self._saturation_tb)
        self._slot_tb = QSpinBox()
        self._slot_tb.setRange(0, 65565)
        layout.addRow("Slot", self._slot_tb)
        layout.addItem(QSpacerItem(0, 25))

        self._button_box = QDialogButtonBox()
        self._button_box.addButton(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.close)
        self._button_box.addButton(QDialogButtonBox.StandardButton.Ok).clicked.connect(self.accept)
        layout.addWidget(self._button_box)
        self.setLayout(layout)

    @override
    def accept(self):
        _ColorMappingListWidgetItem(self._list_widget,
                                    ColorHSI(self._hue_tb.value(), self._saturation_tb.value(), 0.5),
                                    self._slot_tb.value())
        super().accept()


class ColorToColorwheelAdapterSetupWidget(NodeEditorFilterConfigWidget):
    """Configuration widget for color to colorwheel vfilter."""

    def __init__(self, filter: ColorToColorWheel) -> None:
        """Initialize the configuration widget."""
        super().__init__()
        self._input_dialog: _ColorSlotInputDialog | SelectionDialog | None = None
        self._widget = QWidget()
        layout = QFormLayout()

        self._selected_fixture: UsedFixture | None = None
        self._filter = filter

        fixture_selection_container = QWidget(parent=self._widget)
        fixture_selection_container.setLayout(QHBoxLayout())
        self._selected_fixture_label = QLabel("No Fixture Selected.")
        fixture_selection_container.layout().addWidget(self._selected_fixture_label)
        self._fixture_selection_or_clear_button = QPushButton("Select Fixture")
        self._fixture_selection_or_clear_button.clicked.connect(self._load_from_fixture_clicked)
        fixture_selection_container.layout().addWidget(self._fixture_selection_or_clear_button)
        layout.addRow("Selected Fixture: ", fixture_selection_container)
        self._colorwheel_index_spinbox = QSpinBox()
        self._colorwheel_index_spinbox.setMinimum(0)
        self._colorwheel_index_spinbox.setMaximum(255)
        self._colorwheel_index_spinbox.setValue(0)
        self._colorwheel_index_spinbox.setEnabled(False)
        layout.addRow("Color Wheel Index: ", self._colorwheel_index_spinbox)

        layout.addItem(QSpacerItem(0, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))

        self._enable_dimmer_input_cb = QCheckBox("Enable Dimmer Input")
        layout.addRow("Enable Dimmer Input", self._enable_dimmer_input_cb)
        self._dimmer_input_datatype_combobox = QComboBox()
        self._dimmer_input_datatype_combobox.setEditable(False)
        self._dimmer_input_datatype_combobox.addItems(["8bit", "16bit", "float", ""])
        layout.addRow("Dimmer Input Type", self._dimmer_input_datatype_combobox)
        self._dimmer_output_datatype_combobox = QComboBox()
        self._dimmer_output_datatype_combobox.setEditable(False)
        self._dimmer_output_datatype_combobox.addItems(["8bit", "16bit", "float", ""])
        layout.addRow("Dimmer Output Type", self._dimmer_output_datatype_combobox)
        self._colorwheel_datatype_combobox = QComboBox()
        self._colorwheel_datatype_combobox.setEditable(False)
        self._colorwheel_datatype_combobox.addItems(["8bit", "16bit"])
        layout.addRow("Color Wheel Data Type", self._colorwheel_datatype_combobox)

        self._color_mapping_list = QListWidget()
        layout.addWidget(self._color_mapping_list)
        self._mapping_manipulation_buttongroup = QWidget()
        self._mapping_manipulation_buttongroup.setLayout(QHBoxLayout())
        self._mapping_manipulation_buttongroup.layout().addItem(QSpacerItem(
            10, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        ))
        self._add_mapping_button = QPushButton("Add Mapping")
        self._add_mapping_button.clicked.connect(self._add_mapping_clicked)
        self._mapping_manipulation_buttongroup.layout().addWidget(self._add_mapping_button)
        self._remove_mapping_button = QPushButton("Remove Mapping")
        self._remove_mapping_button.clicked.connect(self._remove_mapping_clicked)
        self._mapping_manipulation_buttongroup.layout().addWidget(self._remove_mapping_button)
        layout.addWidget(self._mapping_manipulation_buttongroup)

        self._wheel_speed_spinbox = QSpinBox()
        self._wheel_speed_spinbox.setMinimum(0)
        self._wheel_speed_spinbox.setMaximum(65565)
        self._wheel_speed_spinbox.setValue(300)
        self._wheel_speed_spinbox.setToolTip("How many ms does it take to switch between two adjacent color wheel slots?")
        layout.addRow("Color Wheel Speed [ms]", self._wheel_speed_spinbox)
        self._dimm_when_wheel_is_moving_cb = QCheckBox("Dim when Wheel Moving")
        self._dimm_when_wheel_is_moving_cb.setChecked(True)
        layout.addWidget(self._dimm_when_wheel_is_moving_cb)

        self._widget.setLayout(layout)

    def _add_mapping_clicked(self) -> None:
        self._input_dialog = _ColorSlotInputDialog(self._widget, self._color_mapping_list)
        self._input_dialog.setModal(True)
        self._input_dialog.show()

    def _remove_mapping_clicked(self) -> None:
        items_to_remove = [index for index in self._color_mapping_list.selectedIndexes()]
        items_to_remove.sort(reverse=True)
        for item in items_to_remove:
            self._color_mapping_list.takeItem(item)

    def _load_from_fixture_clicked(self) -> None:
        if self._selected_fixture is not None:
            self._selected_fixture = None
            self._update_selected_fixture()
            return
        fixture_names = [f"[{f.universe_id}:{f.start_index}] {f.name}" for f in self._filter.scene.board_configuration.fixtures]
        self._input_dialog = SelectionDialog("Select Fixture", "Please select the target fixture",
                                             fixture_names, parent=self._widget, multi_selection_allowed=False,
                                             selected_callback=self._fixture_selected_callback)
        self._input_dialog.setModal(True)
        self._input_dialog.show()

    def _fixture_selected_callback(self, sd: SelectionDialog) -> None:
        fixture_univ, fixture_chan = sd.selected_items[0].split("] ", 1)[0].replace("[", "").split(":")
        fixture_chan = int(fixture_chan)
        fixture_univ = int(fixture_univ)
        self._selected_fixture = self._filter.scene.board_configuration.get_fixture_by_address(fixture_univ, fixture_chan)
        self._update_selected_fixture()

    def _parse_color_mapping(self, mapping: str) -> None:
        self._color_mapping_list.clear()
        for entry_str in mapping.split(';'):
            if len(entry_str) == 0:
                continue
            hue, saturation, slot = entry_str.split(':')
            hue = float(hue)
            saturation = float(saturation)
            slot = int(slot)
            _ColorMappingListWidgetItem(self._color_mapping_list, ColorHSI(hue, saturation, 0.5), slot)

    def _update_selected_fixture(self) -> None:
        if self._selected_fixture is None:
            self._fixture_selection_or_clear_button.setText("Select Fixture")
            self._colorwheel_index_spinbox.setEnabled(False)
            self._color_mapping_list.setEnabled(True)
            self._selected_fixture_label.setText("No Fixture Selected.")
            self._remove_mapping_button.setEnabled(True)
            self._add_mapping_button.setEnabled(True)
        else:
            self._fixture_selection_or_clear_button.setText("Clear Selected Fixture")
            self._colorwheel_index_spinbox.setEnabled(len(self._selected_fixture.colorwheel_mappings) > 0)
            self._color_mapping_list.setEnabled(False)
            self._selected_fixture_label.setText(self._selected_fixture.name)
            self._remove_mapping_button.setEnabled(False)
            self._add_mapping_button.setEnabled(False)
            self._parse_color_mapping(extract_colorwheel_mappings_from_fixture(
                self._selected_fixture,
                selected_slot_index=self._colorwheel_index_spinbox.value()
            ))

    def _compile_color_mapping_string(self) -> str:
        parts: list[_ColorMappingListWidgetItem] = []
        for i in range(self._color_mapping_list.count()):
            item = self._color_mapping_list.item(i)
            if not isinstance(item, _ColorMappingListWidgetItem):
                continue
            parts.append(item)
        return ";".join(f"{item.color.hue}:{item.color.saturation}:{item.slot_value}" for item in parts)

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {
            "mode": "automatic" if self._selected_fixture is not None else "manual",
            "fixture-uuid": self._selected_fixture.uuid if self._selected_fixture is not None else "",
            "color-mappings": self._compile_color_mapping_string(),
            "dimmer-input": self._dimmer_input_datatype_combobox.currentText(),
            "dimmer-output": self._dimmer_output_datatype_combobox.currentText(),
            "colorwheel-datatype": self._colorwheel_datatype_combobox.currentText(),
            "wheel_speed": str(self._wheel_speed_spinbox.value()),
            "dim_when_off": str(self._dimm_when_wheel_is_moving_cb.isChecked()),
            "colorwheel-id": str(self._colorwheel_index_spinbox.value()),
        }

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._selected_fixture = self._filter.scene.board_configuration.get_fixture(conf["fixture-uuid"])
        self._parse_color_mapping(conf["color-mappings"])
        self._update_selected_fixture()
        self._dimmer_input_datatype_combobox.setCurrentText(conf["dimmer-input"])
        self._dimmer_output_datatype_combobox.setCurrentText(conf["dimmer-output"])
        self._colorwheel_datatype_combobox.setCurrentText(conf["colorwheel-datatype"])
        self._colorwheel_index_spinbox.setValue(int(conf["colorwheel-id"]))
        self._wheel_speed_spinbox.setValue(int(conf["wheel_speed"]))
        self._dimm_when_wheel_is_moving_cb.setChecked(conf["dim_when_off"] == "true")

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        return parameters  # Nothing to do here

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {}  # Nothing to do here

    @override
    def parent_opened(self) -> None:
        pass  # Nothing to do here