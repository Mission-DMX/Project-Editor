"""Show UI widget to update constant filter values using a slider."""

from __future__ import annotations

import warnings
from logging import getLogger
from math import isfinite
from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from model import Filter, UIPage, UIWidget
from model.filter import DataType, FilterTypeEnumeration

if TYPE_CHECKING:
    import proto.FilterMode_pb2
    from model import Scene

_FLOAT_SLIDER_STEPS = 10000

logger = getLogger(__name__)


def _parse_config_float(raw: str, fallback: float) -> float:
    """Parse a float configuration entry, falling back on malformed input.

    Args:
        raw: The raw configuration value to parse.
        fallback: The value to return instead if the raw value is not a finite number.

    Returns:
        The parsed value, or the fallback for unparseable, NaN or infinite input.

    """
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return fallback
    return value if isfinite(value) else fallback


def _parse_config_int(raw: str, fallback: int) -> int:
    """Parse an integer configuration entry, falling back on malformed input.

    Args:
        raw: The raw configuration value to parse. Decimal fractions are truncated towards zero.
        fallback: The value to return instead if the raw value cannot be converted.

    Returns:
        The parsed value, or the fallback for unparseable input.

    """
    return int(_parse_config_float(raw, float(fallback)))


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
        self._model: Filter | None = None
        self._value: int | float = 0
        self._minimum = 0
        self._maximum = 255
        self._orientation = Qt.Orientation.Horizontal
        self._registered_callback_key: tuple[Scene, str] | None = None
        self._player_slider: QSlider | None = None
        self._value_label: QLabel | None = None
        self._preview_sliders: list[QSlider] = []
        self._preview_labels: list[QLabel] = []
        self._data_type: DataType = DataType.DT_8_BIT
        self._range_min: float = 0.0
        self._range_max: float = 255.0

        # Load configuration if available
        if "orientation" in self._configuration:
            self._orientation = (
                Qt.Orientation.Vertical
                if self._configuration["orientation"] == "vertical"
                else Qt.Orientation.Horizontal
            )

    def __del__(self) -> None:
        """Unregister the fish update callback (fallback in case close was not called)."""
        self._unregister_fish_callback()

    @override
    def close(self) -> None:
        """Unregister the fish update callback as this widget is being removed."""
        self._unregister_fish_callback()

    def _unregister_fish_callback(self) -> None:
        """Remove the update callback registered for the linked filter, if any."""
        # getattr keeps this safe for partially initialized instances whose __del__ runs early.
        registered_key = getattr(self, "_registered_callback_key", None)
        if registered_key is None:
            return
        self._registered_callback_key = None
        scene, filter_id = registered_key
        scene.board_configuration.remove_filter_update_callback(scene, filter_id, self._update_from_fish)

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

        if f.filter_type in (
            FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
            FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT,
        ):
            self._data_type = DataType.DT_8_BIT
            self._setup_integer_slider_range(0.0, 255.0)
            self._value = self._clamp_value(_parse_config_int(f.initial_parameters.get("value", "0"), 0))
        elif f.filter_type in (
            FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
            FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_16BIT,
        ):
            self._data_type = DataType.DT_16_BIT
            self._setup_integer_slider_range(0.0, 65535.0)
            self._value = self._clamp_value(_parse_config_int(f.initial_parameters.get("value", "0"), 0))
        else:  # FILTER_CONSTANT_FLOAT / FILTER_RESPONDING_CONSTANT_FLOAT
            self._data_type = DataType.DT_DOUBLE
            range_min = _parse_config_float(self._configuration.get("min", "0.0"), 0.0)
            range_max = _parse_config_float(self._configuration.get("max", "1.0"), 1.0)
            if range_min >= range_max:
                logger.warning(
                    "Invalid configured slider range [%s, %s] (min >= max), falling back to [0.0, 1.0].",
                    range_min,
                    range_max,
                )
                range_min, range_max = 0.0, 1.0
            self._range_min, self._range_max = range_min, range_max
            self._minimum = 0
            self._maximum = _FLOAT_SLIDER_STEPS
            self._value = self._clamp_value(_parse_config_float(f.initial_parameters.get("value", "0.0"), 0.0))

        self._sync_sliders(reset_bounds=True)

        if self._registered_callback_key != (f.scene, f.filter_id):
            self._unregister_fish_callback()
            f.scene.board_configuration.register_filter_update_callback(f.scene, f.filter_id, self._update_from_fish)
            self._registered_callback_key = (f.scene, f.filter_id)

    def _setup_integer_slider_range(self, default_min: float, default_max: float) -> None:
        """Set up the integer slider range from the widget configuration.

        Args:
            default_min: The lowest allowed and default lower range bound.
            default_max: The highest allowed and default upper range bound.

        """
        range_min = _parse_config_float(self._configuration.get("min", str(default_min)), default_min)
        range_max = _parse_config_float(self._configuration.get("max", str(default_max)), default_max)
        range_min = max(default_min, min(default_max - 1, range_min))
        range_max = max(default_min + 1, min(default_max, range_max))
        if range_min >= range_max:
            logger.warning(
                "Invalid configured slider range [%s, %s] (min >= max), falling back to [%s, %s].",
                range_min,
                range_max,
                default_min,
                default_max,
            )
            range_min, range_max = default_min, default_max
        self._range_min, self._range_max = range_min, range_max
        self._minimum, self._maximum = int(range_min), int(range_max)

    def _value_to_slider_pos(self) -> int:
        """Convert the current value to an integer slider position."""
        if self._data_type == DataType.DT_DOUBLE:
            span = self._range_max - self._range_min
            if span == 0:
                return 0
            frac = (float(self._value) - self._range_min) / span
            return int(max(0, min(_FLOAT_SLIDER_STEPS, frac * _FLOAT_SLIDER_STEPS)))
        return int(self._value)

    def _slider_pos_to_float(self, pos: int) -> float:
        """Convert a slider position to a float value."""
        return self._range_min + (pos / _FLOAT_SLIDER_STEPS) * (self._range_max - self._range_min)

    def _clamp_value(self, value: float) -> float:
        """Clamp a value to the range representable by the slider.

        Args:
            value: The value to clamp.

        Returns:
            The clamped value: bounded by the configured float range for float filters or by
            the integer slider bounds for 8/16 bit filters.

        """
        if self._data_type == DataType.DT_DOUBLE:
            return min(self._range_max, max(self._range_min, float(value)))
        return min(self._maximum, max(self._minimum, int(value)))

    def _sync_sliders(self, *, reset_bounds: bool = False) -> None:
        """Synchronize all tracked sliders and value labels with the current widget state.

        Qt objects that were already destroyed are pruned from the tracking lists. Slider values
        are updated with blocked signals to avoid feedback loops with the update logic.

        Args:
            reset_bounds: Whether to also re-apply the slider minimum and maximum bounds.

        """
        self._player_slider = self._sync_slider(self._player_slider, reset_bounds=reset_bounds)
        self._value_label = self._sync_label(self._value_label)

        alive_preview_sliders: list[QSlider] = []
        for current_slider in self._preview_sliders:
            synced_slider = self._sync_slider(current_slider, reset_bounds=reset_bounds)
            if synced_slider is not None:
                alive_preview_sliders.append(synced_slider)
        self._preview_sliders = alive_preview_sliders

        alive_preview_labels: list[QLabel] = []
        for current_label in self._preview_labels:
            synced_label = self._sync_label(current_label)
            if synced_label is not None:
                alive_preview_labels.append(synced_label)
        self._preview_labels = alive_preview_labels

    def _sync_slider(self, slider: QSlider | None, *, reset_bounds: bool = False) -> QSlider | None:
        """Update a single slider to the current value, pruning it if its Qt object is gone.

        Args:
            slider: The slider to update, or None.
            reset_bounds: Whether to also re-apply the slider minimum and maximum bounds.

        Returns:
            The updated slider, or None if it was None or its Qt object was already destroyed.

        """
        if slider is None:
            return None
        try:
            if reset_bounds:
                slider.setMinimum(self._minimum)
                slider.setMaximum(self._maximum)
            slider.blockSignals(True)
            slider.setValue(self._value_to_slider_pos())
            slider.blockSignals(False)
        except RuntimeError:
            return None  # underlying Qt object was already deleted
        return slider

    def _sync_label(self, label: QLabel | None) -> QLabel | None:
        """Update a single value label, pruning it if its Qt object is gone.

        Args:
            label: The label to update, or None.

        Returns:
            The updated label, or None if it was None or its Qt object was already destroyed.

        """
        if label is None:
            return None
        try:
            label.setText(self._format_value())
        except RuntimeError:
            return None  # underlying Qt object was already deleted
        return label

    def _format_value(self) -> str:
        if self._data_type == DataType.DT_DOUBLE:
            return f"{float(self._value):.4f}"
        return str(self._value)

    def _set_value(self, slider_pos: int) -> None:
        """Update the value from a slider position and push to filter."""
        if self._data_type == DataType.DT_DOUBLE:
            self._value = self._slider_pos_to_float(slider_pos)
        else:
            self._value = slider_pos
        self._sync_sliders()
        self.push_update()

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        """Generate update content for the filter."""
        if self._data_type == DataType.DT_DOUBLE:
            return [("value", f"{float(self._value):.6f}")]
        return [("value", str(self._value))]

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        """Get the player widget with the slider."""
        w = QWidget(parent)
        self._player_widget = self._construct_player_widget(w)

        if self._orientation == Qt.Orientation.Vertical:
            layout = QVBoxLayout()
            layout.addWidget(self._value_label)
            layout.addWidget(self._player_widget)
        else:
            layout = QHBoxLayout()
            layout.addWidget(self._player_widget)
            layout.addWidget(self._value_label)

        w.setLayout(layout)
        w.resize(layout.totalMinimumSize())
        return w

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        """Get the configuration widget for the editor."""
        w = QWidget(parent)
        self._configuration_widget = self._construct_preview_widget(w)
        layout = QVBoxLayout()
        layout.addWidget(self._configuration_widget)
        w.setLayout(layout)
        w.resize(layout.totalMinimumSize())
        return w

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        """Create a deep copy of this widget."""
        w = SliderConstantUIWidget(new_parent, self.configuration.copy())
        super().copy_base(w)
        linked_filter_id = self.associated_filters.get("constant")
        if linked_filter_id is not None:
            linked_filter = new_parent.scene.get_filter_by_id(linked_filter_id)
            if linked_filter is not None:
                w.set_filter(linked_filter, 0)
        return w

    def _construct_player_widget(self, parent: QWidget | None) -> QWidget:
        """Construct the interactive player widget with slider and return it."""
        player_widget = QWidget(parent)

        if self._player_slider is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    self._player_slider.valueChanged.disconnect(self._set_value)
                except (RuntimeError, TypeError):
                    pass  # the old slider was already destroyed or disconnected
        self._player_slider = QSlider(self._orientation, player_widget)
        self._player_slider.setMinimum(self._minimum)
        self._player_slider.setMaximum(self._maximum)
        self._player_slider.setValue(self._value_to_slider_pos())
        self._player_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._player_slider.setTickInterval(max(1, (self._maximum - self._minimum) // 10))
        self._player_slider.valueChanged.connect(self._set_value)

        self._value_label = QLabel(self._format_value(), player_widget)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set layout
        size = _parse_config_int(self._configuration.get("size", "200"), 200)
        if self._orientation == Qt.Orientation.Vertical:
            layout = QVBoxLayout()
            player_widget.setMinimumHeight(size)
            player_widget.setMinimumWidth(80)
        else:
            layout = QHBoxLayout()
            player_widget.setMinimumHeight(80)
            player_widget.setMinimumWidth(size)

        layout.addWidget(self._player_slider)
        player_widget.setLayout(layout)
        return player_widget

    def _construct_preview_widget(self, parent: QWidget | None) -> QWidget:
        """Construct a non-interactive preview of the player widget.

        The preview slider is disabled and not connected to any update logic, so editor views
        never push filter updates to fish.
        """
        preview_widget = QWidget(parent)
        preview_slider = QSlider(self._orientation, preview_widget)
        preview_slider.setMinimum(self._minimum)
        preview_slider.setMaximum(self._maximum)
        preview_slider.setValue(self._value_to_slider_pos())
        preview_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        preview_slider.setTickInterval(max(1, (self._maximum - self._minimum) // 10))
        preview_slider.setEnabled(False)
        self._preview_sliders.append(preview_slider)

        preview_label = QLabel(self._format_value(), preview_widget)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_labels.append(preview_label)

        # Set layout
        size = _parse_config_int(self._configuration.get("size", "200"), 200)
        layout: QVBoxLayout | QHBoxLayout
        if self._orientation == Qt.Orientation.Vertical:
            layout = QVBoxLayout()
            layout.addWidget(preview_label)
            layout.addWidget(preview_slider)
            preview_widget.setMinimumHeight(size)
            preview_widget.setMinimumWidth(80)
        else:
            layout = QHBoxLayout()
            layout.addWidget(preview_slider)
            layout.addWidget(preview_label)
            preview_widget.setMinimumHeight(80)
            preview_widget.setMinimumWidth(size)
        preview_widget.setLayout(layout)
        return preview_widget

    def _construct_configuration_widget(self, parent: QWidget | None) -> QWidget:
        """Construct the configuration controls widget and return it."""
        controls = QWidget(parent)
        layout = QVBoxLayout()
        layout.addWidget(self._construct_preview_widget(None))

        # Orientation selection
        orientation_group = QWidget(controls)
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
        size_group = QWidget(controls)
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Slider Size:", size_group))
        size_spinbox = QSpinBox(size_group)
        size_spinbox.setMinimum(50)
        size_spinbox.setMaximum(500)
        size_spinbox.setValue(_parse_config_int(self._configuration.get("size", "200"), 200))
        size_layout.addWidget(size_spinbox)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # Value range configuration
        range_group = QWidget(controls)
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Min:", range_group))
        if self._data_type == DataType.DT_DOUBLE:
            min_box: QSpinBox | QDoubleSpinBox = QDoubleSpinBox(range_group)
            min_box.setDecimals(4)
            min_box.setRange(-1e9, 1e9)
            min_box.setValue(self._range_min)
            max_box: QSpinBox | QDoubleSpinBox = QDoubleSpinBox(range_group)
            max_box.setDecimals(4)
            max_box.setRange(-1e9, 1e9)
            max_box.setValue(self._range_max)
        else:
            type_hi = 255 if self._data_type == DataType.DT_8_BIT else 65535
            min_box = QSpinBox(range_group)
            min_box.setRange(0, type_hi - 1)
            min_box.setValue(int(self._range_min))
            max_box = QSpinBox(range_group)
            max_box.setRange(1, type_hi)
            max_box.setValue(int(self._range_max))
        range_layout.addWidget(min_box)
        range_layout.addWidget(QLabel("Max:", range_group))
        range_layout.addWidget(max_box)
        range_group.setLayout(range_layout)
        layout.addWidget(range_group)

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
            self._configuration["size"] = str(new_size)
            for widget in filter(None, [self._player_widget, self._configuration_widget]):
                if self._orientation == Qt.Orientation.Vertical:
                    widget.setMinimumHeight(new_size)
                else:
                    widget.setMinimumWidth(new_size)
                outer = widget.parent()
                ancestor = outer
                while ancestor is not None:
                    if hasattr(ancestor, "update_size") and callable(ancestor.update_size):
                        ancestor.update_size()
                        if outer is not None and outer is not ancestor:
                            outer.resize(ancestor.size())
                        break
                    ancestor = ancestor.parent()

        size_spinbox.valueChanged.connect(update_size)

        def update_min(new_min: float) -> None:
            new_min_f = float(new_min)
            if new_min_f >= self._range_max:
                return
            self._range_min = new_min_f
            self._configuration["min"] = str(new_min_f)
            if self._data_type != DataType.DT_DOUBLE:
                self._minimum = int(new_min_f)
            self._value = self._clamp_value(self._value)
            self._sync_sliders(reset_bounds=True)

        def update_max(new_max: float) -> None:
            new_max_f = float(new_max)
            if new_max_f <= self._range_min:
                return
            self._range_max = new_max_f
            self._configuration["max"] = str(new_max_f)
            if self._data_type != DataType.DT_DOUBLE:
                self._maximum = int(new_max_f)
            self._value = self._clamp_value(self._value)
            self._sync_sliders(reset_bounds=True)

        min_box.valueChanged.connect(update_min)
        max_box.valueChanged.connect(update_max)

        controls.setLayout(layout)
        return controls

    def __str__(self) -> str:
        """Get the filter id string or an error message."""
        return str(self._model.filter_id if self._model else "Error: No Filter configured.")

    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Update slider position based on filter updates from fish."""
        if param.parameter_key != "value":
            return
        if self._data_type == DataType.DT_DOUBLE:
            self._value = self._clamp_value(_parse_config_float(param.parameter_value, float(self._value)))
        else:
            self._value = self._clamp_value(_parse_config_int(param.parameter_value, int(self._value)))
        self._sync_sliders()

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        """Get the configuration dialog widget."""
        w = QWidget(parent)
        controls = self._construct_configuration_widget(w)
        layout = QVBoxLayout()
        layout.addWidget(controls)
        w.setLayout(layout)
        return w
