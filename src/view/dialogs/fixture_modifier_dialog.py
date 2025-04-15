# coding=utf-8
"""Dialog for modifying fixtures"""
from PySide6 import QtGui, QtWidgets

from model import PatchingUniverse
from model.patching_channel import PatchingChannel


class FixtureModifierDialog(QtWidgets.QDialog):
    """Dialog for modifying fixtures"""

    def __init__(self, patching_channel: PatchingChannel, universe: PatchingUniverse, parent: object = None) -> None:
        """Dialog for modifying fixtures"""
        super().__init__(parent)
        self._patching_channel = patching_channel
        self._patching_universe = universe

        name_on_stage_layout = QtWidgets.QHBoxLayout()
        _name_on_stage_label = QtWidgets.QLabel("Name on Stage")
        self._name_on_stage = QtWidgets.QLineEdit(patching_channel.fixture.name_on_stage)
        name_on_stage_layout.addWidget(_name_on_stage_label)
        name_on_stage_layout.addWidget(self._name_on_stage)

        color_layout = QtWidgets.QHBoxLayout()
        _color_layout_label = QtWidgets.QLabel("Color")
        self._color = QtWidgets.QLineEdit(patching_channel.color)
        color_layout.addWidget(_color_layout_label)
        color_layout.addWidget(self._color)

        channel_layout = QtWidgets.QHBoxLayout()
        _channel_label = QtWidgets.QLabel("Start Channel")
        self._channel = QtWidgets.QLineEdit(str(patching_channel.fixture.first_channel + 1))
        self._channel.setValidator(QtGui.QIntValidator(1, 512))
        self._channel.textChanged.connect(self._validate_input)
        channel_layout.addWidget(_channel_label)
        channel_layout.addWidget(self._channel)

        layout_exit = QtWidgets.QHBoxLayout()
        self._ok = QtWidgets.QPushButton()
        self._ok.setText("OK")
        _cancel = QtWidgets.QPushButton()
        _cancel.setText("cancel")
        self._remove = QtWidgets.QCheckBox()
        self._remove.setText("remove")
        layout_exit.addWidget(self._remove)
        layout_exit.addWidget(_cancel)
        layout_exit.addWidget(self._ok)
        _cancel.setAutoDefault(False)
        self._ok.setAutoDefault(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(name_on_stage_layout)
        layout.addLayout(color_layout)
        layout.addLayout(channel_layout)
        layout.addLayout(layout_exit)

        self.setLayout(layout)
        self._ok.clicked.connect(self._accept)
        _cancel.clicked.connect(self._reject)
        self._validate_input()

    @property
    def remove(self):
        """property for remove is checked"""
        return self._remove.isChecked()

    @property
    def name_on_stage(self):
        """property for name_on_stage"""
        return self._name_on_stage.text()

    @property
    def color(self):
        """property for color"""
        # TODO colorpicker
        return self._color.text()

    @property
    def channel(self):
        """property for channel with default 0"""
        try:
            return int(self._channel.text()) - 1
        except ValueError:
            return 0

    def _accept(self) -> None:
        """accept the Fixture"""
        self.accept()

    def _reject(self) -> None:
        """cancel the Fixture"""
        self.reject()

    def _validate_input(self) -> None:
        """validate the input of channel """
        start_channel = self.channel
        length = len(self._patching_channel.fixture.channels)

        self._ok.setEnabled(False)
        if 51 <= start_channel + length:
            return
        for i in range(length):
            if not (self._patching_universe.patching[start_channel + i].fixture.name == "Empty" or
                    self._patching_universe.patching[start_channel + i].fixture == self._patching_channel.fixture):
                return

        self._ok.setEnabled(True)
