# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
from abc import ABC
from typing import Callable, TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QSpinBox, QWidget, QLabel, QHBoxLayout

from model import UIWidget

if TYPE_CHECKING:
    from model import UIPage


class _DebugVizWidget(UIWidget, ABC):

    """This class is the foundation for widgets that display the state of remote debug nodes"""

    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
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
        w = QWidget()
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


class ColorDebugVizWidget(_DebugVizWidget):
    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
        super().__init__(parent, configuration)
        self.configured_dimensions_changed_callback = self._dimensions_changed
        # TODO register update message listener

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        # TODO construct and return visualization widget
        pass

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        # TODO implement
        pass

    def _dimensions_changed(self):
        pass  # TODO change dimensions of show widget, if it exists


