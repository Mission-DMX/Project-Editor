"""Provides configuration widget for Color2Colorwheel adapter."""

from __future__ import annotations

from typing import override, TYPE_CHECKING

from PySide6.QtWidgets import QWidget, QFormLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox, QListWidget, \
    QSpinBox, QSpacerItem, QSizePolicy

from model.ofl.fixture import UsedFixture
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget

if TYPE_CHECKING:
    from view.show_mode.editor.nodes import FilterNode
    from model.virtual_filters.color_to_colorwheel import ColorToColorWheel, extract_colorwheel_mappings_from_fixture


class ColorToColorwheelAdapterSetupWidget(NodeEditorFilterConfigWidget):
    """Configuration widget for color to colorwheel vfilter."""

    def __init__(self, filter: ColorToColorWheel) -> None:
        """Initialize the configuration widget."""
        super().__init__()
        self._widget = QWidget()
        layout = QFormLayout()

        self._selected_fixture: UsedFixture | None = None
        self._filter = filter

        fixture_selection_container = QWidget(parent=self._widget)
        fixture_selection_container.setLayout(QHBoxLayout())
        self._selected_fixture_label = QLabel("No Fixture Selected.")
        fixture_selection_container.layout().addWidget(self._selected_fixture_label)
        self._fixture_selection_or_clear_button = QPushButton("Select Fixture")
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
        # TODO add options and disable other texts
        layout.addRow("Dimmer Input Type", self._dimmer_input_datatype_combobox)
        self._dimmer_output_datatype_combobox = QComboBox()
        # TODO add options and disable other texts
        layout.addRow("Dimmer Output Type", self._dimmer_output_datatype_combobox)
        self._colorwheel_datatype_combobox = QComboBox()
        # TODO add options and disable other texts
        layout.addRow("Color Wheel Data Type", self._colorwheel_datatype_combobox)

        self._color_mapping_list = QListWidget()
        layout.addWidget(self._color_mapping_list)
        # TODO add buttons for addition and removal of mappings

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

    def _load_from_fixture_clicked(self) -> None:
        # TODO show selection dialog with callback self._update_selected_fixture
        pass

    def _parse_color_mapping(self, mapping: str) -> None:
        # TODO clear and populate color mapping table
        pass

    def _update_selected_fixture(self) -> None:
        if self._selected_fixture is None:
            self._fixture_selection_or_clear_button.setText("Select Fixture")
            self._colorwheel_index_spinbox.setEnabled(False)
            self._color_mapping_list.setEnabled(True)
            self._selected_fixture_label.setText("No Fixture Selected.")
        else:
            self._fixture_selection_or_clear_button.setText("Clear Selected Fixture")
            self._colorwheel_index_spinbox.setEnabled(len(self._selected_fixture.colorwheel_mappings) > 0)
            self._color_mapping_list.setEnabled(False)
            self._selected_fixture_label.setText(self._selected_fixture.name)
        # TODO disable mapping management buttons if selected fixture is not None
        self._parse_color_mapping(extract_colorwheel_mappings_from_fixture(
            self._selected_fixture,
            selected_slot_index=self._colorwheel_index_spinbox.value()
        ))

    def _compile_color_mapping_string(self) -> str:
        return ""  # TODO

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
        pass  # Nothing to do here

    @override
    def _get_parameters(self) -> dict[str, str]:
        pass  # Nothing to do here

    @override
    def parent_opened(self) -> None:
        pass  # Nothing to do here