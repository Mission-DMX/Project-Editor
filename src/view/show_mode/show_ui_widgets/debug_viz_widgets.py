# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
from abc import ABC
from logging import getLogger
from typing import Callable, TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtGui import QPaintEvent, QPainter, QBrush, QColor
from PySide6.QtWidgets import QFormLayout, QSpinBox, QWidget, QLabel, QHBoxLayout, QComboBox

from model import UIWidget, ColorHSI
from proto.FilterMode_pb2 import update_parameter

if TYPE_CHECKING:
    from model import UIPage


logger = getLogger(__file__)

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

    def __del__(self):
        if self._config_widget is not None:
            self._config_widget.deleteLater()
        if self._placeholder_widget is not None:
            self._placeholder_widget.deleteLater()

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
            presentation_mode_box.setCurrentText(self.configuration.get("mode") or self.presentation_mode[0])
            presentation_mode_box.currentTextChanged.connect(self._mode_conf_changed)
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

    def _mode_conf_changed(self, new_mode_str: str):
        """Change the configured mode and call dimensions changed callback if any."""
        self.configuration["mode"] = new_mode_str
        if self.configured_dimensions_changed_callback is not None:
            self.configured_dimensions_changed_callback()


class _ColorLabel(QWidget):

    """A label for displaying colors"""

    def __init__(self, *args, **kwargs):
        """Default color is black"""
        super().__init__(*args, **kwargs)
        self._last_color: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._last_color_processed: QColor = QColor()

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
        self._last_color_processed = ColorHSI(h, s, i).to_qt_color()
        self.update()

    def paintEvent(self, event: QPaintEvent, /):
        """Redraw the widget"""
        painter = QPainter(self)
        c = self._last_color_processed
        r = event.rect()
        painter.drawRect(r.x(), r.y(), r.width(), r.height())
        painter.fillRect(r.x() + 1, r.y() + 1, r.width() - 2, r.height() - 2, c)
        painter.end()


class ColorDebugVizWidget(_DebugVizWidget):
    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
        super().__init__(parent, configuration)
        self.configured_dimensions_changed_callback = self._dimensions_changed
        self._show_widget: _ColorLabel | None = None

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._show_widget is None:
            self._construct_player_widget(parent)
        return self._show_widget

    def _construct_player_widget(self, parent: QWidget):
        w = _ColorLabel(parent=parent)
        w.setFixedWidth(self.configured_width)
        w.setFixedHeight(self.configured_height)
        self._show_widget = w
        self.parent.scene.board_configuration.register_filter_update_callback(
            self.parent.scene.scene_id, self.filter_ids[0], self._recv_update)
        self._show_widget.destroyed.connect(self._delete_callback)

    def _delete_callback(self):
        if self._show_widget is not None:
            self.parent.scene.board_configuration.remove_filter_update_callback(
                self.parent.scene.scene_id, self.filter_ids[0], self._recv_update
            )
            self._show_widget.deleteLater()

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
        else:
            try:
                hsi_value = param.parameter_value.split(",")
                self._show_widget.set_hsi(float(hsi_value[0]), float(hsi_value[1]), float(hsi_value[2]))
            except ValueError:
                logger.error(f"Unable to parse color '{param.parameter_value}' from filter '{param.filter_id}:"
                             f"{param.parameter_key}'.")


class _NumberLabel(QWidget):
    def __init__(self, *args, **kwargs):
        """Default number is 0, default mode is without illumination display"""
        super().__init__(*args, **kwargs)
        self.mode: str = ""
        self._number: float = 0.0
        self._text: str = "0"

    def paintEvent(self, event: QPaintEvent, /):
        """Redraw the widget"""
        painter = QPainter(self)
        painter.drawRect(0, 0, self.width(), self.height())
        if self.mode == "Illumination":
            alpha = self._number / 255.0
            indicator_color = QColor.fromRgbF(1.0, 1.0, 0, alpha)
            painter.fillRect(1, 1, self.width() - 2, self.height() - 2, indicator_color)
        fm = painter.fontMetrics()
        painter.drawText(
            int(self.width() / 2 - fm.horizontalAdvance(self._text) / 2),
            int(self.height() / 2 - fm.height() / 2), self._text)
        painter.end()

    @property
    def number(self) -> float:
        return self._number

    @number.setter
    def number(self, new_number: int | float):
        if new_number == self._number:
            return
        text = f"{new_number:.5f}"
        while text[-1] == '0' and '.' in text:
            text = text[:-1]
        if text[-1] == '.':
            text = text[:-1]
        if text == self._text:
            return
        self._text = text
        self._number = new_number
        self.update()


class NumberDebugVizWidget(_DebugVizWidget):
    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
        super().__init__(parent, configuration, ["Plain", "Illumination"])
        self._show_widget: _NumberLabel | None = None
        self.configured_dimensions_changed_callback = self._dimensions_changed

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._show_widget is None:
            self._show_widget = _NumberLabel(parent)
            self._dimensions_changed()
            self.parent.scene.board_configuration.register_filter_update_callback(
                self.parent.scene.scene_id, self.filter_ids[0], self._recv_update)
            self._show_widget.destroyed.connect(self._delete_callback)
        return self._show_widget

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        c = NumberDebugVizWidget(new_parent, self.configuration.copy())
        super().copy_base(c)
        return c

    def _dimensions_changed(self):
        if self._show_widget is None:
            return
        self._show_widget.setFixedWidth(self.configured_width)
        self._show_widget.setFixedHeight(self.configured_height)
        self._show_widget.mode = self.configuration.get("mode") or "Plain"

    def _recv_update(self, param: update_parameter):
        """Checks for correct filter and updates the displayed number"""
        if self._show_widget is None:
            return
        else:
            try:
                self._show_widget.number = float(param.parameter_value)
            except ValueError:
                logger.error(f"Unexpected number received from filter '{param.filter_id}:{param.parameter_key}': "
                             f"{param.parameter_value}")

    def _delete_callback(self):
        if self._show_widget is not None:
            self.parent.scene.board_configuration.remove_filter_update_callback(self.parent.scene.scene_id, self.filter_ids[0], self._recv_update)
            self._show_widget.deleteLater()
