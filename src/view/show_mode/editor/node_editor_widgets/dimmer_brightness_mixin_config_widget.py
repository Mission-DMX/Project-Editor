from typing import override

from PySide6.QtWidgets import QButtonGroup, QCheckBox, QFormLayout, QHBoxLayout, QLabel, QRadioButton, QWidget

from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget


class DimmerBrightnessMixinConfigWidget(NodeEditorFilterConfigWidget):
    """Configuration widget for dimmer brightness mixin node."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Load the filter and prepare a widget."""
        super().__init__()
        self._widget = QWidget(parent=parent)
        layout = QFormLayout()
        self._cb_has_16bit = QCheckBox(self._widget)
        self._cb_has_16bit.setText("Enable 16bit output")
        self._cb_has_16bit.checkStateChanged.connect(self._update_warning_visibility)
        layout.addWidget(self._cb_has_16bit)
        self._cb_has_8bit = QCheckBox(self._widget)
        self._cb_has_8bit.setText("Enable 8bit output")
        self._cb_has_8bit.checkStateChanged.connect(self._update_warning_visibility)
        layout.addWidget(self._cb_has_8bit)
        self._output_warning_label = QLabel("At least one output should be configured.", self._widget)
        self._output_warning_label.setVisible(False)
        self._output_warning_label.setStyleSheet("color: red;")
        layout.addWidget(self._output_warning_label)

        self._input_method_rb_group = QButtonGroup(self._widget)
        self._input_8bit = QRadioButton("8bit", self._widget)
        self._input_method_rb_group.addButton(self._input_8bit)
        self._input_16bit = QRadioButton("16bit", self._widget)
        self._input_method_rb_group.addButton(self._input_16bit)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self._input_8bit)
        button_layout.addWidget(self._input_16bit)
        layout.addRow("Input Port Data Type:", button_layout)

        self._mixin_method_rb_group = QButtonGroup(self._widget)
        self._mixin_8bit = QRadioButton("8bit", self._widget)
        self._mixin_method_rb_group.addButton(self._mixin_8bit)
        self._mixin_16bit = QRadioButton("16bit", self._widget)
        self._mixin_method_rb_group.addButton(self._mixin_16bit)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self._mixin_8bit)
        button_layout.addWidget(self._mixin_16bit)
        layout.addRow("Mixin Port Data Type:", button_layout)

        self._widget.setLayout(layout)

    def _update_warning_visibility(self) -> None:
        self._output_warning_label.setVisible(not self._cb_has_8bit.isChecked() and not self._cb_has_16bit.isChecked())

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {
            "has_16bit_output": "true" if self._cb_has_16bit.isChecked() else "false",
            "has_8bit_output": "true" if self._cb_has_8bit.isChecked() else "false",
            "input_method": "8bit" if self._input_8bit.isChecked() else "16bit",
            "input_method_mixin": "8bit" if self._mixin_8bit.isChecked() else "16bit",
        }

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._cb_has_16bit.setChecked(conf.get("has_16bit_output", "false") == "true")
        self._cb_has_8bit.setChecked(conf.get("has_8bit_output", "false") == "true")
        self._input_8bit.setChecked(conf.get("input_method", "8bit") == "8bit")
        self._input_16bit.setChecked(conf.get("input_method", "8bit") == "16bit")
        self._mixin_8bit.setChecked(conf.get("input_method_mixin", "8bit") == "8bit")
        self._mixin_16bit.setChecked(conf.get("input_method_mixin", "8bit") == "16bit")

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        # Nothing to do here
        pass

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {}

    @override
    def parent_opened(self) -> None:
        # Nothing to do here
        pass
