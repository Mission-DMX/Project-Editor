"""Widget to edit a channel."""
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QWidget

import style
from model.channel import Channel
from model.control_desk import BankSet
from model.patching.fixture_channel import FixtureChannel
from view.console_mode.console_fader_bank_selector import ConsoleFaderBankSelectorWidget


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

    def __init__(self, fixture_channel: FixtureChannel, channel: Channel, bank_set: BankSet = None,
                 bank_set_control_list: list[QWidget] | None = None, parent: QWidget = None) -> None:
        """Inits the ChannelWidget.

        Args:
            channel: The channel this widget represents.
            parent: Qt parent of the widget
        """
        super().__init__(parent=parent)
        if bank_set_control_list is None:
            bank_set_control_list = []
        self._channel = channel

        # general width and height for all components
        element_size = 40

        # specific length of the slider
        slider_len = 256

        # Displays the address of the channel + 1 for human readability
        address_label: QtWidgets.QLabel = QtWidgets.QLabel(str(self._channel.address + 1), self)
        address_label.setFixedSize(element_size, element_size)
        address_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Displays the current channel value
        self._value_editor: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        self._value_editor.setValue(self._channel.value)
        self._value_editor.setMaximum(255)
        self._value_editor.setMinimum(0)
        self._value_editor.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._value_editor.setFixedSize(element_size, element_size)
        self._value_editor.textChanged.connect(self.update_value)
        self._value_editor.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self._fixture_channel = QtWidgets.QLabel(fixture_channel.name)
        self._fixture_channel.setWordWrap(True)
        self._fixture_channel.setFixedSize(element_size, element_size * 2)
        self._fixture_channel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self._channel.updated.connect(self.update_value)

        self._bank_selector = ConsoleFaderBankSelectorWidget(bank_set, fixture_channel.name,
                                                             bank_set_control_list=bank_set_control_list)
        self._bank_selector.fader_value_changed.connect(self.update_value)
        self._bank_selector.setFixedWidth(element_size)

        # Button to set the channel to the max value 255
        self._max_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Max", self)
        self._max_button.setFixedSize(element_size, element_size)
        self._max_button.setStyleSheet(style.BUTTON)
        self._max_button.clicked.connect(lambda: self.update_value(255))

        # Slider to change the value and display the current value graphically
        # direction = QtCore.Qt.Horizontal if draw_horizontally else QtCore.Qt.Vertical
        self._slider: QtWidgets.QSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Vertical, self)
        self._slider.setSingleStep(1)
        self._slider.setPageStep(1)
        self._slider.setMinimum(0)
        self._slider.setMaximum(255)
        self._slider.setFixedSize(element_size, slider_len)
        self._slider.setStyleSheet(style.SLIDER)
        self._slider.valueChanged.connect(self.update_value)

        # Button to set the channel to the min value 0
        self._min_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Min", self)
        self._min_button.setFixedSize(element_size, element_size)
        self._min_button.setStyleSheet(style.ACTIVE_BUTTON)
        self._min_button.clicked.connect(lambda: self.update_value(0))

        self._channel.updated.connect(self._update)

        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(address_label)
        layout.addWidget(self._fixture_channel)
        layout.addWidget(self._bank_selector)
        layout.addWidget(self._value_editor)
        layout.addWidget(self._max_button)
        layout.addWidget(self._slider)
        layout.addWidget(self._min_button)

        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)

    def _update(self, value: int) -> None:
        """Updates the slider and value label."""
        self._slider.setValue(value)
        self._value_editor.setValue(value)
        if value == 0:
            self._min_button.setStyleSheet(style.ACTIVE_BUTTON)
            self._max_button.setStyleSheet(style.BUTTON)
        elif value == 255:
            self._max_button.setStyleSheet(style.ACTIVE_BUTTON)
            self._min_button.setStyleSheet(style.BUTTON)
        else:
            self._min_button.setStyleSheet(style.BUTTON)
            self._max_button.setStyleSheet(style.BUTTON)

    def update_value(self, value: int | str) -> None:
        """update of a value in """
        value = int(value)
        self._bank_selector._latest_ui_position_update = value
        if self._channel.value != value:
            value = min(max(value, 0), 255)
            self._channel.value = value
            self._bank_selector.fader_value_changed.emit(value)
