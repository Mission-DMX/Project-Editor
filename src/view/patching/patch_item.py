# coding=utf-8
""" item of the Patching """
from PySide6 import QtWidgets

from Style import Style
from model.patching_channel import PatchingChannel
from model.patching_universe import PatchingUniverse


class PatchItem(QtWidgets.QFrame):
    """a single item of the PatchPlan"""

    def __init__(self, channel: PatchingChannel, universe: PatchingUniverse):
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
        self._channel.updated_color.connect(lambda color: self._update_color(color))
        self._channel.updated_fixture.connect(self._update_fixture)
        self._update_fixture()
        self._update_color(self._channel.color)

    def _update_color(self, color: str) -> None:
        """
        update color of an item
        Args:
            color: new color
        """
        self.setStyleSheet(Style.PATCH + f"background-color: {color};")

    def _update_fixture(self) -> None:
        """update fixture of a item"""
        self._fixture_name.setText(self._channel.fixture.name)
        self._fixture_channel.setText(self._channel.fixture_channel)
        self.setToolTip(f"{self._channel.fixture.name}\n{self._channel.fixture_channel}")
