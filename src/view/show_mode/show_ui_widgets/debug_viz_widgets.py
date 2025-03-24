# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
from abc import ABC
from typing import Callable, TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtGui import QPaintEvent, QPainter, QBrush, QColor
from PySide6.QtWidgets import QFormLayout, QSpinBox, QWidget, QLabel, QHBoxLayout, QComboBox

from model import UIWidget, ColorHSI
from proto.FilterMode_pb2 import update_parameter

if TYPE_CHECKING:
    from model import UIPage


class _DebugVizWidget(UIWidget, ABC):

    """This class is the foundation for widgets that display the state of remote debug nodes"""

    def __init__(self, parent: "UIPage", configuration: dict[str, str], presentation_mode: list[str] | None = None):
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

    def generate_update_content(self) -> list[tuple[str, str]]:
        # As we only consume values, we do not need to generate updates
        return []

    def get_config_dialog_widget(self, parent: QWidget | None) -> QWidget:
        if self._config_widget is None:
            self._construct_config_widget()
        return self._config_widget

    def set_conf_width(self, new_width: int):
        """
        This method updates the configured width.
        Passing 0 or negative numbers will abort execution.
        :param new_width: The width to set.
        """
        if new_width < 1:
            return
        self.configured_width = new_width
        self.configuration["width"] = str(new_width)
        if self.configured_dimensions_changed_callback is not None:
            self.configured_dimensions_changed_callback()
        if self._placeholder_widget is not None:
            self._placeholder_widget.setFixedWidth(new_width)

    def set_conf_height(self, new_height: int):
        """
        This method updates the configured height.
        Passing 0 or negative numbers will abort execution.
        :param new_height: The height to set.
        """
        if new_height < 1:
            return
        self.configured_height = new_height
        self.configuration["height"] = str(new_height)
        if self.configured_dimensions_changed_callback is not None:
            self.configured_dimensions_changed_callback()
        if self._placeholder_widget is not None:
            self._placeholder_widget.setFixedHeight(new_height)

    def _construct_config_widget(self):
        """This method constructs the widget for dimension and display mode setup."""
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
            # TODO load correct mode from config and set it
        else:
            presentation_mode_box.setEnabled(False)
        layout.addRow("Presentation Mode: ", presentation_mode_box)
        w.setLayout(layout)
        self._config_widget = w

    def get_configuration_widget(self, parent: QWidget) -> QWidget:
        if self._placeholder_widget is not None:
            return self._placeholder_widget
        w = QWidget(parent=parent)
        w.setFixedWidth(self.configured_width)
        w.setFixedHeight(self.configured_height)
        w.setStyleSheet("background-color: #505050;")
        layout = QHBoxLayout()
        layout.addWidget(QLabel(",".join(self.filter_ids)))
        w.setLayout(layout)
        self._placeholder_widget = w
        return w


class _ColorLabel(QWidget):

    """A label for displaying colors"""

    def __init__(self, *args, **kwargs):
        """Default color is black"""
        super().__init__(*args, **kwargs)
        self._last_color: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def set_hsi(self, h: float, s: float, i: float):
        """
        Set the color of the color label.
        :param h: The hue value
        :param s: The saturation value
        :param i: The luminescence value
        """
        if self._last_color == (h, s, i):
            return
        self._last_color = (h, s, i)
        self.update()

    def paintEvent(self, event: QPaintEvent, /):
        """Redraw the widget"""
        painter = QPainter(self)
        c = self._last_color
        r = event.rect()
        painter.drawRect(r.x(), r.y(), r.width(), r.height())
        painter.fillRect(r.x(), r.y(), r.width(), r.height(), ColorHSI(c[0], c[1], c[2]).to_qt_color())
        painter.end()


class ColorDebugVizWidget(_DebugVizWidget):
    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
        super().__init__(parent, configuration)
        self.configured_dimensions_changed_callback = self._dimensions_changed
        self._show_widget: _ColorLabel | None = None
        parent.scene.board_configuration.broadcaster.update_filter_parameter.connect(self._recv_update)

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._show_widget is None:
            self._construct_player_widget(parent)
        return self._show_widget

    def _construct_player_widget(self, parent: QWidget):
        w = _ColorLabel(parent=parent)
        w.setFixedWidth(self.configured_width)
        w.setFixedHeight(self.configured_height)
        self._show_widget = w

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        c = ColorDebugVizWidget(new_parent, self.configuration.copy())
        super().copy_base(c)
        return c

    def _dimensions_changed(self):
        if self._show_widget is None:
            return
        self._show_widget.setFixedWidth(self.configured_width)
        self._show_widget.setFixedHeight(self.configured_height)

    def _recv_update(self, param: update_parameter):
        """Checks for correct filter and updates the displayed color"""
        if self._show_widget is None:
            return
        if param.filter_id == self.filter_ids[0]:
            try:
                print(param.parameter_value)
                hsi_value = param.parameter_value.split(",")
                self._show_widget.set_hsi(float(hsi_value[0]), float(hsi_value[1]), float(hsi_value[2]))
            except ValueError:
                pass
