# coding=utf-8
""" item of the Patching """
from PySide6 import QtWidgets

from DMXModel import Channel, Universe


class PatchItem(QtWidgets.QFrame):
    def __init__(self, channel: Channel, universe: Universe):
        super().__init__()
        self._channel: Channel = channel
        self._universe = universe
        self.setFixedSize(80, 80)
        self.setStyleSheet("background-color: rgb(0,0,0); border:1px solid rgb(255, 255, 255); ")
        address_label: QtWidgets.QLabel = QtWidgets.QLabel(str(channel.address+1), self)
        address_label.setFixedSize(40, 20)
        self._device_name: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self._chanel_value: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self._device_name.move(0, address_label.height())
        self._chanel_value.move(address_label.width(), 0)
        self.update()

    def update(self):
        self._device_name.setText(self._channel.device.name)
        self._chanel_value.setText(str(self._channel.value))

