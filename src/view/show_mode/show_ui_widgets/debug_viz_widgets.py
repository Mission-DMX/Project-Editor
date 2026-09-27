# SPDX-License-Identifier: GPL-3.0-or-later
"""Debug output show UI widgets.

ColorLabel -- Regular Qt Widget to display set color.
ColorDebugVizWidget -- Show UI widget to display debug output containing colors.
NumberDebugVizWidget -- Show UI widget to display debug output containing numbers.
"""

from __future__ import annotations

from abc import ABC
from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QSpinBox, QWidget

from model import FilterUpdateCallbackMixin, UIWidget
from model.color_hsi import ColorHSI
from model.filter import FilterTypeEnumeration

if TYPE_CHECKING:
    from collections.abc import Callable

    import proto.FilterMode_pb2
    from model import Filter, UIPage

logger = getLogger(__name__)


class _DebugVizWidget(FilterUpdateCallbackMixin, UIWidget, ABC):
    """Provide the foundation for widgets that display the state of remote debug nodes."""

    def __init__(
        self, parent: UIPage, configuration: dict[str, str], presentation_mode: list[str] | None = None
    ) -> None:
        super().__init__(parent, configuration)
        self._config_widget: QWidget | None = None
        self._placeholder_widget: QWidget | None = None
        self.configured_dimensions_changed_callback: Callable | None = None
        try:
            self.configured_height = int(configuration.get("height") or "50")
            self.configured_width = int(configuration.get("width") or "100")
        except ValueError:
            self.configured_height = 50
            configuration["height"] = "50"
            self.configured_width = 100
            configuration["width"] = "100"
        self.presentation_mode = presentation_mode

    @override
    def set_filter(self, f: Filter, i: int) -> None:
        """Link the debug widget to a filter and start listening to its fish updates."""
        if not f:
            return
        super().set_filter(f, i)
        self._register_fish_callback(f)

    @override
    def notify_id_rename(self, old_id: str, new_id: str) -> None:
        """Move the linked filter id and the fish callback along when the filter is renamed."""
        super().notify_id_rename(old_id, new_id)
        self._handle_filter_id_rename(old_id, new_id)

    def __del__(self) -> None:
        try:
            if self._config_widget is not None:
                self._config_widget.deleteLater()
            if self._placeholder_widget is not None:
                self._placeholder_widget.deleteLater()
        except (RuntimeError, AttributeError):
            pass
        super().__del__()

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        # As we only consume values, we do not need to generate updates
        return []

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        if self._config_widget is not None:
            self._config_widget.deleteLater()
        self._construct_config_widget()
        return self._config_widget

    def set_conf_width(self, new_width: int) -> None:
        """Update the configured width.

        Passing 0 or negative numbers will abort execution.

        Args:
            new_width:  The width to set.

        """
        if new_width < 1:
            return
        self.configured_width = new_width
        self.configuration["width"] = str(new_width)
        if self.configured_dimensions_changed_callback is not None:
            self.configured_dimensions_changed_callback()
        if self._placeholder_widget is not None:
            self._placeholder_widget.setFixedWidth(new_width)

    def set_conf_height(self, new_height: int) -> None:
        """Update the configured height.

        Passing 0 or negative numbers will abort execution.

        Args:
            new_height:  The height to set.

        """
        if new_height < 1:
            return
        self.configured_height = new_height
        self.configuration["height"] = str(new_height)
        if self.configured_dimensions_changed_callback is not None:
            self.configured_dimensions_changed_callback()
        if self._placeholder_widget is not None:
            self._placeholder_widget.setFixedHeight(new_height)

    def _construct_config_widget(self) -> None:
        """Construct the widget for dimension and display mode setup."""
        w = QWidget()
        w.setMinimumWidth(250)
        w.setMinimumHeight(125)
        layout = QFormLayout()
        width_widget = QSpinBox()
        width_widget.setMinimum(0)
        width_widget.setMaximum(1000)
        width_widget.setValue(self.configured_width)
        width_widget.valueChanged.connect(self.set_conf_width)
        layout.addRow("Width:", width_widget)
        height_widget = QSpinBox()
        height_widget.setMinimum(0)
        height_widget.setMaximum(1000)
        height_widget.setValue(self.configured_height)
        height_widget.valueChanged.connect(self.set_conf_height)
        layout.addRow("Height:", height_widget)
        presentation_mode_box = QComboBox()
        if self.presentation_mode is not None:
            presentation_mode_box.addItems(self.presentation_mode)
            presentation_mode_box.setCurrentText(self.configuration.get("mode") or self.presentation_mode[0])
            presentation_mode_box.currentTextChanged.connect(self._mode_conf_changed)
        else:
            presentation_mode_box.setEnabled(False)
        layout.addRow("Presentation Mode: ", presentation_mode_box)
        w.setLayout(layout)
        self._config_widget = w

    @override
    def get_configuration_widget(self, parent: QWidget) -> QWidget:
        if self._placeholder_widget is not None:
            self._placeholder_widget.deleteLater()
        w = QWidget(parent=parent)
        w.setFixedWidth(self.configured_width)
        w.setFixedHeight(self.configured_height)
        w.setStyleSheet("background-color: #505050;")
        layout = QHBoxLayout()
        layout.addWidget(QLabel(",".join(self.filter_ids)))
        w.setLayout(layout)
        self._placeholder_widget = w
        return w

    def _mode_conf_changed(self, new_mode_str: str) -> None:
        """Change the configured mode and call dimensions changed callback if any."""
        self.configuration["mode"] = new_mode_str
        if self.configured_dimensions_changed_callback is not None:
            self.configured_dimensions_changed_callback()


class ColorLabel(QWidget):
    """Label for displaying colors."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Label for displaying colors.

        Default color is black.
        """
        super().__init__(parent)
        self._last_color: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._last_color_processed: QColor = QColor()
        self.setMinimumWidth(16)
        self.setMinimumHeight(16)

    def set_color(self, c: ColorHSI) -> None:
        """Set the color to display.

        Args:
            c: The color to set. (ColorHSI)

        """
        if not isinstance(c, ColorHSI):
            raise ValueError(f"Failed to set color. Expected ColorHSI, got {type(c)}.")
        self.set_hsi(c.hue, c.saturation, c.intensity)

    def set_hsi(self, h: float, s: float, i: float) -> None:
        """Set the color of the color label.

        Args:
            h: The hue value.
            s: The saturation value.
            i: The luminescence value.

        """
        if self._last_color == (h, s, i):
            return
        self._last_color = (h, s, i)
        self._last_color_processed = ColorHSI(h, s, i).to_qt_color()
        self.update()

    @override
    def paintEvent(self, event: QPaintEvent, /) -> None:
        """Redraw the widget."""
        painter = QPainter(self)
        c = self._last_color_processed
        r = event.rect()
        painter.drawRect(r.x(), r.y(), r.width(), r.height())
        painter.fillRect(r.x() + 1, r.y() + 1, r.width() - 2, r.height() - 2, c)
        painter.end()

    def get_color(self) -> ColorHSI:
        """Get the color currently displayed."""
        return ColorHSI(self._last_color[0], self._last_color[1], self._last_color[2])


class ColorDebugVizWidget(_DebugVizWidget):
    """Show UI widget to display debug output colors."""

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize show UI widget using parent UI page and configuration."""
        super().__init__(parent, configuration)
        self.configured_dimensions_changed_callback = self._dimensions_changed
        self._show_widget: ColorLabel | None = None

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        self._construct_player_widget(parent)
        return self._show_widget

    def _construct_player_widget(self, parent: QWidget) -> None:
        w = ColorLabel(parent=parent)
        w.setFixedWidth(self.configured_width)
        w.setFixedHeight(self.configured_height)
        self._show_widget = w

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        c = ColorDebugVizWidget(new_parent, self.configuration.copy())
        super().copy_base(c)
        return c

    def _dimensions_changed(self) -> None:
        if self._show_widget is None:
            return
        self._show_widget.setFixedWidth(self.configured_width)
        self._show_widget.setFixedHeight(self.configured_height)

    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Check for correct filter and updates the displayed color."""
        if self._show_widget is None:
            return

        try:
            hsi_value = param.parameter_value.split(",")
            self._show_widget.set_hsi(float(hsi_value[0]), float(hsi_value[1]), float(hsi_value[2]))
        except ValueError:
            logger.exception(
                "Unable to parse color '%s' from filter '%s:%s'.",
                param.parameter_value,
                param.filter_id,
                param.parameter_key,
            )
        except RuntimeError:
            self._show_widget = None


class _NumberLabel(QWidget):
    def __init__(self, parent: QWidget | None, is_16bit: bool) -> None:
        super().__init__(parent)
        self.mode: str = ""
        self._number: float = 0.0
        self._text: str = "0"
        self._divider: float = 65535.0 if is_16bit else 255.0

    @override
    def paintEvent(self, event: QPaintEvent, /) -> None:
        """Redraw the widget."""
        painter = QPainter(self)
        painter.drawRect(0, 0, self.width(), self.height())
        if self.mode == "Illumination":
            alpha = self._number / self._divider
            indicator_color = QColor.fromRgbF(1.0, 1.0, 0, alpha)
            painter.fillRect(1, 1, self.width() - 2, self.height() - 2, indicator_color)
        fm = painter.fontMetrics()
        painter.drawText(
            int(self.width() / 2 - fm.horizontalAdvance(self._text) / 2),
            int(self.height() / 2 - fm.height() / 2),
            self._text,
        )
        painter.end()

    @property
    def number(self) -> float:
        return self._number

    @number.setter
    def number(self, new_number: float) -> None:
        if new_number == self._number:
            return
        text = f"{new_number:.5f}"
        while text[-1] == "0" and "." in text:
            text = text[:-1]
        if text[-1] == ".":
            text = text[:-1]
        if text == self._text:
            return
        self._text = text
        self._number = new_number
        self.update()


class NumberDebugVizWidget(_DebugVizWidget):
    """UI widget to display debug output numbers."""

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize widget using parent UI page and initial configuration data."""
        super().__init__(parent, configuration, ["Plain", "Illumination"])
        self._show_widget: _NumberLabel | None = None
        self.configured_dimensions_changed_callback = self._dimensions_changed

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        linked_filter = self.parent.scene.get_filter_by_id(self.filter_ids[0]) if self.filter_ids else None
        self._show_widget = _NumberLabel(
            parent,
            linked_filter is not None and linked_filter.filter_type == FilterTypeEnumeration.FILTER_REMOTE_DEBUG_16BIT,
        )
        self._dimensions_changed()
        return self._show_widget

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        c = NumberDebugVizWidget(new_parent, self.configuration.copy())
        super().copy_base(c)
        return c

    def _dimensions_changed(self) -> None:
        if self._show_widget is None:
            return
        self._show_widget.setFixedWidth(self.configured_width)
        self._show_widget.setFixedHeight(self.configured_height)
        self._show_widget.mode = self.configuration.get("mode") or "Plain"

    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Check for correct filter and updates the displayed number."""
        if self._show_widget is None:
            return

        try:
            self._show_widget.number = float(param.parameter_value)
        except ValueError:
            logger.exception(
                "Unexpected number received from filter '%s:%s': %s",
                param.filter_id,
                param.parameter_key,
                param.parameter_value,
            )
        except RuntimeError:
            self._show_widget = None

    def __del__(self) -> None:
        """Clean up the number label on object deletion."""
        if self._show_widget is not None:
            try:
                self._show_widget.deleteLater()
            except RuntimeError:
                pass  # The Qt widget was already destroyed.
            self._show_widget = None
        super().__del__()
