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

from model import Filter, FilterUpdateCallbackMixin, UIPage, UIWidget
from model.filter import DataType, FilterTypeEnumeration
from view.show_mode.editor.editor_tab_widgets.ui_widget_editor._widget_holder import UIWidgetHolder

if TYPE_CHECKING:
    import proto.FilterMode_pb2

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


def _set_spin_box_value(box: QSpinBox | QDoubleSpinBox, value: float) -> float:
    """Set a spin box value without re-triggering its valueChanged handlers.

    Args:
        box: The spin box to update.
        value: The value to set. Integer spin boxes truncate towards zero, double spin boxes
            round to their configured number of decimals.

    Returns:
        The effective value now shown by the spin box, to keep the applied state in sync with
        the display.

    """
    box.blockSignals(True)
    if isinstance(box, QSpinBox):
        box.setValue(int(value))
    else:
        box.setValue(value)
    effective_value = float(box.value())
    box.blockSignals(False)
    return effective_value


class SliderConstantUIWidget(FilterUpdateCallbackMixin, UIWidget):
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
        self._player_slider: QSlider | None = None
        self._value_label: QLabel | None = None
        self._previews: list[tuple[QSlider | None, QLabel | None]] = []
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

    def set_filter(self, f: Filter, i: int) -> None:
        """Set the filter associated with this UI widget.

        Args:
            f: The new filter to set
            i: The index to update (unused for slider, always 0).

        """
        if not f:
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
        self._register_fish_callback(f)

    @override
    def notify_id_rename(self, old_id: str, new_id: str) -> None:
        """Move the linked constant filter id and the fish callback along when the filter is renamed."""
        super().notify_id_rename(old_id, new_id)
        self._handle_filter_id_rename(old_id, new_id)

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
        self._value_label = self._sync_label(self._value_label, self._value)

        alive_previews: list[tuple[QSlider | None, QLabel | None]] = []
        for current_slider, current_label in self._previews:
            synced_slider = self._sync_slider(current_slider, reset_bounds=reset_bounds)
            synced_label = self._sync_label(current_label, self._value)
            if synced_slider is not None or synced_label is not None:
                alive_previews.append((synced_slider, synced_label))
        self._previews = alive_previews

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
            slider.blockSignals(True)
            if reset_bounds:
                slider.setMinimum(self._minimum)
                slider.setMaximum(self._maximum)
            slider.setValue(self._value_to_slider_pos())
            slider.blockSignals(False)
        except RuntimeError:
            return None  # underlying Qt object was already deleted
        return slider

    def _sync_label(self, label: QLabel | None, value: float) -> QLabel | None:
        """Update a single value label, pruning it if its Qt object is gone.

        Args:
            label: The label to update, or None.
            value: The value whose formatted representation to display.

        Returns:
            The updated label, or None if it was None or its Qt object was already destroyed.

        """
        if label is None:
            return None
        try:
            label.setText(self._format_value(value))
        except RuntimeError:
            return None  # underlying Qt object was already deleted
        return label

    def _format_value(self, value: float) -> str:
        """Format a value for display according to the linked filter's data type."""
        if self._data_type == DataType.DT_DOUBLE:
            return f"{float(value):.4f}"
        return str(value)

    def _set_value(self, slider_pos: int) -> None:
        """Update the value from a slider position and push to filter.

        The player slider has tracking disabled, so this is invoked when the handle is
        released or on keyboard and wheel input - not for every intermediate drag position.
        """
        if self._data_type == DataType.DT_DOUBLE:
            self._value = self._slider_pos_to_float(slider_pos)
        else:
            self._value = slider_pos
        self._sync_sliders()
        self.push_update()

    def _preview_slider_position(self, pos: int) -> None:
        """Update the value label from an in-progress drag position without committing the state.

        The player slider has tracking disabled, so ``valueChanged`` (and with it the state commit
        and the filter update push) is only emitted when the handle is released. This handler only
        previews the drag position in the value label; the widget state itself is committed by
        ``_set_value`` once the handle is released, so an aborted drag cannot desynchronize it.

        Args:
            pos: The slider position of the ongoing drag.

        """
        preview_value = self._slider_pos_to_float(pos) if self._data_type == DataType.DT_DOUBLE else pos
        self._value_label = self._sync_label(self._value_label, preview_value)

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
        layout = QVBoxLayout()
        layout.addWidget(self._player_widget)
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

    def _tick_position(self) -> QSlider.TickPosition:
        """Get the tick position matching the current slider orientation."""
        if self._orientation == Qt.Orientation.Vertical:
            return QSlider.TickPosition.TicksLeft
        return QSlider.TickPosition.TicksBelow

    def _construct_player_widget(self, parent: QWidget | None) -> QWidget:
        """Construct the interactive player widget with slider and return it.

        The slider of a previous call, if any, is disconnected and scheduled for deletion.
        """
        player_widget = QWidget(parent)

        if self._player_slider is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    self._player_slider.valueChanged.disconnect(self._set_value)
                    self._player_slider.sliderMoved.disconnect(self._preview_slider_position)
                except (RuntimeError, TypeError):
                    pass  # the old slider was already destroyed or disconnected
            try:
                self._player_slider.deleteLater()
            except RuntimeError:
                pass  # the old slider was already destroyed
        self._player_slider = QSlider(self._orientation, player_widget)
        self._player_slider.setMinimum(self._minimum)
        self._player_slider.setMaximum(self._maximum)
        self._player_slider.setValue(self._value_to_slider_pos())
        self._player_slider.setTickPosition(self._tick_position())
        self._player_slider.setTickInterval(max(1, (self._maximum - self._minimum) // 10))
        self._player_slider.setTracking(False)
        self._player_slider.sliderMoved.connect(self._preview_slider_position)
        self._player_slider.valueChanged.connect(self._set_value)

        self._value_label = QLabel(self._format_value(self._value), player_widget)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set layout
        size = _parse_config_int(self._configuration.get("size", "200"), 200)
        layout: QVBoxLayout | QHBoxLayout
        if self._orientation == Qt.Orientation.Vertical:
            layout = QVBoxLayout()
            layout.addWidget(self._value_label)
            layout.addWidget(self._player_slider)
            player_widget.setMinimumHeight(size)
            player_widget.setMinimumWidth(80)
        else:
            layout = QHBoxLayout()
            layout.addWidget(self._player_slider)
            layout.addWidget(self._value_label)
            player_widget.setMinimumHeight(80)
            player_widget.setMinimumWidth(size)

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
        preview_slider.setTickPosition(self._tick_position())
        preview_slider.setTickInterval(max(1, (self._maximum - self._minimum) // 10))
        preview_slider.setEnabled(False)

        preview_label = QLabel(self._format_value(self._value), preview_widget)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._previews.append((preview_slider, preview_label))

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

    def _apply_orientation_to_widgets(self) -> None:
        """Apply the current orientation to all already constructed widgets.

        The player widget and every preview widget are rebuilt in place within their parent layouts
        so that sliders, value labels and layout directions match the new orientation. Qt objects
        that were already destroyed are skipped; they are pruned from the tracking lists on the next
        sync. The enclosing widget holders are notified about the changed geometry so that they can
        resize themselves.
        """
        self._rebuild_player_widget()
        for old_slider, old_label in list(self._previews):
            if old_slider is not None:
                self._rebuild_preview_widget(old_slider, old_label)
        self._notify_size_change()

    def _rebuild_player_widget(self) -> None:
        """Rebuild the player widget in place to match the current orientation.

        The old player widget is replaced within its parent layout and destroyed. Nothing happens if
        no player widget was constructed yet or if its Qt object was already destroyed.
        """
        old_widget = self._player_widget
        if old_widget is None:
            return
        try:
            parent = old_widget.parentWidget()
            if parent is None:
                return
            layout = parent.layout()
            if layout is None:
                return
            self._player_widget = self._construct_player_widget(parent)
            layout.replaceWidget(old_widget, self._player_widget)
            old_widget.deleteLater()
        except RuntimeError:
            return

    def _rebuild_preview_widget(self, old_slider: QSlider, old_label: QLabel | None) -> None:
        """Rebuild the preview widget of the given slider in place to match the current orientation.

        The old preview widget is replaced within its parent layout and destroyed, and the tracking
        list entry is replaced by the new slider and label. Nothing happens if the old Qt objects
        were already destroyed.

        Args:
            old_slider: The tracked preview slider whose preview widget to rebuild.
            old_label: The value label tracked alongside the slider, if any.

        """
        try:
            old_widget = old_slider.parentWidget()
            if old_widget is None:
                return
            parent = old_widget.parentWidget()
            if parent is None:
                return
            layout = parent.layout()
            if layout is None:
                return
            new_widget = self._construct_preview_widget(parent)
            if self._configuration_widget is old_widget:
                self._configuration_widget = new_widget
            layout.replaceWidget(old_widget, new_widget)
            old_widget.deleteLater()
            try:
                self._previews.remove((old_slider, old_label))
            except ValueError:
                pass
        except RuntimeError:
            return

    def _apply_minimum_sizes(self) -> None:
        """Apply the configured slider size as the minimum extents of the constructed widgets.

        The widget holding the slider is given the configured size along the slider axis and a
        minimum extent of 80 pixels across it, mirroring the initial widget construction.
        """
        size = _parse_config_int(self._configuration.get("size", "200"), 200)
        vertical = self._orientation == Qt.Orientation.Vertical
        containers: list[QWidget] = [
            widget for widget in (self._player_widget, self._configuration_widget) if widget is not None
        ]
        for slider, _ in self._previews:
            if slider is None:
                continue
            try:
                container = slider.parentWidget()
            except RuntimeError:
                continue
            if container is not None:
                containers.append(container)
        for widget in containers:
            try:
                if vertical:
                    widget.setMinimumHeight(size)
                    widget.setMinimumWidth(80)
                else:
                    widget.setMinimumHeight(80)
                    widget.setMinimumWidth(size)
            except RuntimeError:
                continue

    def _notify_size_change(self) -> None:
        """Inform the enclosing widget holders about changed widget dimensions."""
        for widget in (self._player_widget, self._configuration_widget):
            if widget is None:
                continue
            try:
                ancestor: QWidget | None = widget.parentWidget()
                while ancestor is not None:
                    if isinstance(ancestor, UIWidgetHolder):
                        ancestor.update_size()
                        break
                    ancestor = ancestor.parentWidget()
            except RuntimeError:
                continue

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
        min_box: QSpinBox | QDoubleSpinBox
        max_box: QSpinBox | QDoubleSpinBox
        if self._data_type == DataType.DT_DOUBLE:
            double_min_box = QDoubleSpinBox(range_group)
            double_min_box.setDecimals(4)
            double_min_box.setRange(-1e9, 1e9)
            double_min_box.setValue(self._range_min)
            double_max_box = QDoubleSpinBox(range_group)
            double_max_box.setDecimals(4)
            double_max_box.setRange(-1e9, 1e9)
            double_max_box.setValue(self._range_max)
            min_box = double_min_box
            max_box = double_max_box
        else:
            type_hi = 255 if self._data_type == DataType.DT_8_BIT else 65535
            int_min_box = QSpinBox(range_group)
            int_min_box.setRange(0, type_hi - 1)
            int_min_box.setValue(int(self._range_min))
            int_max_box = QSpinBox(range_group)
            int_max_box.setRange(1, type_hi)
            int_max_box.setValue(int(self._range_max))
            min_box = int_min_box
            max_box = int_max_box
        range_layout.addWidget(min_box)
        range_layout.addWidget(QLabel("Max:", range_group))
        range_layout.addWidget(max_box)
        range_warning_label = QLabel(range_group)
        range_warning_label.setText("Range bounds were adjusted to keep the minimum below the maximum.")
        range_warning_label.setWordWrap(True)
        range_warning_label.setStyleSheet("color: #cc5500;")
        range_warning_label.setVisible(False)
        range_layout.addWidget(range_warning_label)
        range_group.setLayout(range_layout)
        layout.addWidget(range_group)

        range_gap = 10.0 ** -min_box.decimals() if isinstance(min_box, QDoubleSpinBox) else 1.0

        # Connect signals
        def update_orientation() -> None:
            if horizontal_radio.isChecked():
                self._orientation = Qt.Orientation.Horizontal
                self._configuration["orientation"] = "horizontal"
            else:
                self._orientation = Qt.Orientation.Vertical
                self._configuration["orientation"] = "vertical"
            self._apply_orientation_to_widgets()

        horizontal_radio.toggled.connect(update_orientation)
        vertical_radio.toggled.connect(update_orientation)

        def update_size(new_size: int) -> None:
            self._configuration["size"] = str(new_size)
            self._apply_minimum_sizes()
            self._notify_size_change()

        size_spinbox.valueChanged.connect(update_size)

        def update_min(new_min: float) -> None:
            new_min_f = float(new_min)
            if new_min_f >= self._range_max:
                new_min_f = _set_spin_box_value(min_box, self._range_max - range_gap)
                range_warning_label.setVisible(True)
            else:
                range_warning_label.setVisible(False)
            self._range_min = new_min_f
            self._configuration["min"] = str(new_min_f)
            if self._data_type != DataType.DT_DOUBLE:
                self._minimum = int(new_min_f)
            self._value = self._clamp_value(self._value)
            self._sync_sliders(reset_bounds=True)

        def update_max(new_max: float) -> None:
            new_max_f = float(new_max)
            if new_max_f <= self._range_min:
                new_max_f = _set_spin_box_value(max_box, self._range_min + range_gap)
                range_warning_label.setVisible(True)
            else:
                range_warning_label.setVisible(False)
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
