"""Show UI widget to update constant filter values using a slider."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from model import Filter, UIPage, UIWidget
from model.filter import FilterTypeEnumeration

if TYPE_CHECKING:
    import proto.FilterMode_pb2


class SliderConstantUIWidget(UIWidget):
    """Show UI widget to provide the user with a slider that alters the content of a constant filter."""

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Slider UI widget.

        Args:
            parent: The parent widget page.
            configuration: The configuration of this widget.

        """
        super().__init__(parent, configuration)
        self._player_widget: QWidget | None = None
        self._configuration_widget: QWidget | None = None
        self._model = None
        self._value = 0
        self._minimum = 0
        self._maximum = 255
        self._orientation = Qt.Orientation.Horizontal
        self._ui_update_callback_initialized = False
        self._player_slider: QSlider | None = None
        self._value_label: QLabel | None = None

        # Load configuration if available
        if "orientation" in self._configuration:
            self._orientation = (
                Qt.Orientation.Vertical
                if self._configuration["orientation"] == "vertical"
                else Qt.Orientation.Horizontal
            )

    def __del__(self) -> None:
        """Unregister callbacks."""
        if self._ui_update_callback_initialized and self._model is not None:
            self._model.scene.board_configuration.remove_filter_update_callback(
                self._model.scene.scene_id,
                self._model.filter_id,
                self._update_from_fish
            )

    def set_filter(self, f: Filter, i: int) -> None:
        """Set the filter associated with this UI widget.

        Args:
            f: The new filter to set
            i: The index to update (unused for slider, always 0).

        """
        if f is None:
            return
        super().set_filter(f, i)
        self._model = f
        self.associated_filters["constant"] = f.filter_id

        # Set value range based on filter type
        if f.filter_type in [FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
                             FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT]:
            self._minimum = 0
            self._maximum = 255
            self._value = int(f.initial_parameters.get("value", "0"))
        elif f.filter_type in [FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
                               FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_16BIT]:
            self._minimum = 0
            self._maximum = (2 ** 16) - 1
            self._value = int(f.initial_parameters.get("value", "0"))
        else:  # FILTER_CONSTANT_FLOAT
            self._minimum = 0
            self._maximum = 1000  # Default range for float, can be configured
            self._value = float(f.initial_parameters.get("value", "0.0"))

        # Update slider if it exists
        if self._player_slider is not None:
            self._player_slider.setMinimum(self._minimum)
            self._player_slider.setMaximum(self._maximum)
            self._player_slider.setValue(int(self._value))
            if self._value_label is not None:
                self._value_label.setText(str(self._value))

        if not self._ui_update_callback_initialized:
            f.scene.board_configuration.register_filter_update_callback(
                f.scene, f.filter_id, self._update_from_fish
            )
            self._ui_update_callback_initialized = True

    def _set_value(self, new_value: int) -> None:
        """Update the value and push to filter."""
        self._value = new_value
        if self._value_label is not None:
            self._value_label.setText(str(new_value))
        self.push_update()

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        """Generate update content for the filter."""
        return [("value", str(self._value))]

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        """Get the player widget with the slider."""
        w = QWidget(parent)
        self._construct_player_widget(w)

        if self._orientation == Qt.Orientation.Vertical:
            layout = QVBoxLayout()
            layout.addWidget(self._value_label)
            layout.addWidget(self._player_widget)
        else:
            layout = QHBoxLayout()
            layout.addWidget(self._player_widget)
            layout.addWidget(self._value_label)

        w.setLayout(layout)
        return w

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        """Get the configuration widget for the editor."""
        w = QWidget(parent)
        self._construct_configuration_widget(w)
        layout = QVBoxLayout()
        layout.addWidget(self._configuration_widget)
        w.setLayout(layout)
        return w

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        """Create a deep copy of this widget."""
        w = SliderConstantUIWidget(new_parent, self.configuration.copy())
        super().copy_base(w)
        return w

    def _construct_player_widget(self, parent: QWidget | None) -> None:
        """Construct the player widget with slider."""
        self._player_widget = QWidget(parent)

        # Create slider
        self._player_slider = QSlider(self._orientation, self._player_widget)
        self._player_slider.setMinimum(self._minimum)
        self._player_slider.setMaximum(self._maximum)
        self._player_slider.setValue(int(self._value))
        self._player_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._player_slider.setTickInterval(max(1, (self._maximum - self._minimum) // 10))

        # Connect slider value changed signal
        self._player_slider.valueChanged.connect(self._set_value)

        # Create value label
        self._value_label = QLabel(str(self._value), self._player_widget)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set layout
        if self._orientation == Qt.Orientation.Vertical:
            layout = QVBoxLayout()
            self._player_widget.setMinimumHeight(200)
            self._player_widget.setMinimumWidth(80)
        else:
            layout = QHBoxLayout()
            self._player_widget.setMinimumHeight(80)
            self._player_widget.setMinimumWidth(200)

        layout.addWidget(self._player_slider)
        self._player_widget.setLayout(layout)

    def _construct_configuration_widget(self, parent: QWidget | None) -> None:
        """Construct the configuration widget for the editor."""
        if self._player_widget is None:
            self._construct_player_widget(None)
        self._configuration_widget = QWidget(parent)
        layout = QVBoxLayout()

        # Orientation selection
        orientation_group = QWidget(self._configuration_widget)
        orientation_layout = QVBoxLayout()
        orientation_layout.addWidget(QLabel("Orientation:", orientation_group))

        horizontal_radio = QRadioButton("Horizontal", orientation_group)
        vertical_radio = QRadioButton("Vertical", orientation_group)

        # Set current orientation
        if self._orientation == Qt.Orientation.Horizontal:
            horizontal_radio.setChecked(True)
        else:
            vertical_radio.setChecked(True)

        orientation_layout.addWidget(horizontal_radio)
        orientation_layout.addWidget(vertical_radio)
        orientation_group.setLayout(orientation_layout)
        layout.addWidget(orientation_group)

        # Slider size configuration
        size_group = QWidget(self._configuration_widget)
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Slider Size:", size_group))

        size_spinbox = QSpinBox(size_group)
        size_spinbox.setMinimum(50)
        size_spinbox.setMaximum(500)
        size_spinbox.setValue(
            self._player_widget.minimumHeight() if self._orientation == Qt.Orientation.Vertical
            else self._player_widget.minimumWidth()
        )
        size_layout.addWidget(size_spinbox)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # Connect signals
        def update_orientation() -> None:
            if horizontal_radio.isChecked():
                self._orientation = Qt.Orientation.Horizontal
                self._configuration["orientation"] = "horizontal"
            else:
                self._orientation = Qt.Orientation.Vertical
                self._configuration["orientation"] = "vertical"

        horizontal_radio.toggled.connect(update_orientation)
        vertical_radio.toggled.connect(update_orientation)

        def update_size(new_size: int) -> None:
            if self._orientation == Qt.Orientation.Vertical:
                self._player_widget.setMinimumHeight(new_size)
            else:
                self._player_widget.setMinimumWidth(new_size)

        size_spinbox.valueChanged.connect(update_size)

        self._configuration_widget.setLayout(layout)

    def __str__(self) -> str:
        """Get the filter id string or an error message."""
        return str(self._model.filter_id if self._model else "Error: No Filter configured.")

    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Update slider position based on filter updates from fish."""
        if param.parameter_key != "value":
            return

        try:
            new_value = int(float(param.parameter_value))
            if self._player_slider is not None:
                # Block signals to prevent recursive updates
                self._player_slider.blockSignals(True)
                self._player_slider.setValue(new_value)
                self._player_slider.blockSignals(False)

                if self._value_label is not None:
                    self._value_label.setText(str(new_value))

                self._value = new_value
        except (ValueError, TypeError):
            pass  # Ignore invalid values

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        """Get the configuration dialog widget."""
        # Reuse the configuration widget for the dialog
        return self.get_configuration_widget(parent)
