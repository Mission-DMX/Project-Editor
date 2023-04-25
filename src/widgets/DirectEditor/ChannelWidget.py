# coding=utf-8
"""Widget to edit a channel."""
from PySide6 import QtWidgets, QtCore

from Network import NetworkManager
from src.DMXModel import Channel, Universe
from src.Style import Style


class ChannelWidget(QtWidgets.QWidget):
    """Widget to edit a channel.

    Contains address label, value label, min/max buttons and slider.
    Slider allows to choose value between 0 and 255.
    Max button sets value to 255.
    Max button sets value to 0.
    Updates linked channel upon change and monitors linked channels updated signal.

    The widget can be drawn horizontally. It will be aligned to the left side.
    The min button is on the left side, the max button on the right side of the slider.
    """

    def __init__(self, channel: Channel, universe: Universe, fisch_connector: NetworkManager,
                 draw_horizontally: bool = False, parent=None):
        """Inits the ChannelWidget.

        Args:
            channel: The channel this widget represents.
            draw_horizontally: Flag if the widget should be drawn horizontally.
            parent: Qt parent of the widget
        """
        super().__init__(parent=parent)

        # general width and height for all components
        element_size = 35

        # specific length of the slider
        slider_len = 256

        # The associated dmx channel
        self._channel: Channel = channel

        self._universe = universe

        self._fisch_connector = fisch_connector

        # Displays the address of the channel + 1 for human readability
        self._address_label: QtWidgets.QLabel = QtWidgets.QLabel(str(channel.address + 1), self)

        # Displays the current channel value
        self._value_editor: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        self._value_editor.setValue(channel.value)
        self._value_editor.setMaximum(255)
        self._value_editor.setMinimum(0)
        self._value_editor.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self._value_editor.textChanged.connect(self.update_value)

        # Button to set the channel to the max value 255
        self._max_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Max", self)

        # Slider to change the value and display the current value graphically
        direction = QtCore.Qt.Horizontal if draw_horizontally else QtCore.Qt.Vertical
        self._slider: QtWidgets.QSlider = QtWidgets.QSlider(direction, self)

        # Button to set the channel to the min value 0
        self._min_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Min", self)

        # Widget      Height
        # Address     30
        # Value       30
        # Max Button  30
        # Slider      256
        # Min Button  30

        self._channel.updated.connect(lambda x: self._update(x))

        # Offset to address_label -- value_label and value_label -- max/min button
        dx = element_size if draw_horizontally else 0
        dy = 0 if draw_horizontally else element_size

        self._address_label.setFixedSize(element_size, element_size)
        self._address_label.move(0, 0)
        self._address_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self._value_editor.setFixedSize(element_size, element_size)
        self._value_editor.move(self._address_label.x() + dx, self._address_label.y() + dy)
        self._value_editor.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Slider format depending on if widget is vertical or horizontal
        slider_pos_x = (self._value_editor.x() + 2 * dx) if draw_horizontally else 0
        slider_pos_y = 0 if draw_horizontally else (self._value_editor.y() + 2 * dy)
        slider_width = slider_len if draw_horizontally else element_size
        slider_height = element_size if draw_horizontally else slider_len

        self._slider.setMinimum(0)
        self._slider.setMaximum(255)
        self._slider.setFixedSize(slider_width, slider_height)
        self._slider.move(slider_pos_x, slider_pos_y)
        self._slider.setStyleSheet(Style.SLIDER)
        self._slider.valueChanged.connect(lambda x: self.update_value(x))

        # Position of max and min button changes when the widget is shown horizontally
        max_btn_pos_x = (self._slider.x() + slider_len) if draw_horizontally else 0
        max_btn_pos_y = 0 if draw_horizontally else (self._value_editor.y() + element_size)
        min_btn_pos_x = (self._value_editor.x() + element_size) if draw_horizontally else 0
        min_btn_pos_y = 0 if draw_horizontally else (self._slider.y() + slider_len)

        self._max_button.setFixedSize(element_size, element_size)
        self._max_button.move(max_btn_pos_x, max_btn_pos_y)
        self._max_button.setStyleSheet(Style.BUTTON)
        self._max_button.clicked.connect(lambda: self.update_value(255))

        self._min_button.setFixedSize(element_size, element_size)
        self._min_button.move(min_btn_pos_x, min_btn_pos_y)
        self._min_button.setStyleSheet(Style.ACTIVE_BUTTON)
        self._min_button.clicked.connect(lambda: self.update_value(0))

        # Set widget position and size depending on its components and direction
        pos_x = (channel.address * 60) if draw_horizontally else 0
        pos_y = 0 if draw_horizontally else (channel.address * 60)
        width = self._value_editor.width() + self._address_label.width() + self._max_button.width() + self._slider.width() + self._min_button.width() if draw_horizontally else element_size
        height = element_size if draw_horizontally else self._value_editor.height() + self._address_label.height() + self._max_button.height() + self._slider.height() + self._min_button.height()
        self.setFixedSize(width, height)
        self.move(pos_x, pos_y)
        self.setContentsMargins(0, 0, 0, 0)

    def _update(self, value: int) -> None:
        """Updates the slider and value label."""
        self._slider.setValue(value)
        self._value_editor.setValue(value)
        if value == 0:
            self._min_button.setStyleSheet(Style.ACTIVE_BUTTON)
            self._max_button.setStyleSheet(Style.BUTTON)
        elif value == 255:
            self._max_button.setStyleSheet(Style.ACTIVE_BUTTON)
            self._min_button.setStyleSheet(Style.BUTTON)
        else:
            self._min_button.setStyleSheet(Style.BUTTON)
            self._max_button.setStyleSheet(Style.BUTTON)

    def update_value(self, v: int | str):
        v = int(v)
        if self._channel.value != v:
            self._channel.value = v
            self._fisch_connector.send_universe(self._universe)
