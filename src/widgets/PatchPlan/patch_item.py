# coding=utf-8
""" item of the Patching """
from PySide6 import QtWidgets

from DMXModel import PatchingChannel, Universe
from Style import Style


class PatchItem(QtWidgets.QFrame):
    """a single item of the PatchPlan"""

    def __init__(self, channel: PatchingChannel, universe: Universe):
        super().__init__()
        self._channel: PatchingChannel = channel
        self._universe = universe
        self.setFixedSize(100, 80)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        address_label: QtWidgets.QLabel = QtWidgets.QLabel(str(channel.address + 1), self)
        address_label.setFixedSize(40, 20)
        self._fixture_name: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self._fixture_channel: QtWidgets.QLabel = QtWidgets.QLabel(self)
        layout.addWidget(address_label)
        layout.addWidget(self._fixture_name)
        layout.addWidget(self._fixture_channel)
        self.setLayout(layout)
        self.update_patching()

    def update_patching(self) -> None:
        """update patch item after patching"""
        self._fixture_name.setText(self._channel.fixture.name)
        self._fixture_channel.setText(self._channel.fixture_channel)
        self.setStyleSheet(Style.PATCH + f"background-color: {self._channel.color};")
