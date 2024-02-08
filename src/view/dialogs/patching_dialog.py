# coding=utf-8
""" Dialog for Patching Fixture"""

import re

from PySide6 import QtWidgets, QtGui, QtCore
from dataclasses import dataclass
from controller.ofl.fixture import Fixture, UsedFixture, make_used_fixture


@dataclass
class PatchingInformation:
    """Information for Patching"""

    def __init__(self, used_fixture: UsedFixture):
        self.used_fixture = used_fixture
        self.count: int = 0
        self.universe: int = 0
        self.channel: int = 0
        self.offset: int = 0


class PatchingDialog(QtWidgets.QDialog):
    """ Dialog for Patching Fixture """

    def __init__(self, fixture: tuple[Fixture, int], parent: object = None) -> None:
        super().__init__(parent)
        # Create widgets
        self._fixture: Fixture = fixture[0]
        self._patching_information = PatchingInformation(make_used_fixture(self._fixture, 0, -1))

        layout_fixture = QtWidgets.QHBoxLayout()
        self._select_mode = QtWidgets.QComboBox()
        self._select_mode.currentIndexChanged.connect(self._update_used_fixture)
        layout_fixture.addWidget(QtWidgets.QLabel(fixture[0]['name']))
        layout_fixture.addWidget(self._select_mode)

        patching_layout = QtWidgets.QHBoxLayout()
        _patching_node = QtWidgets.QLabel("Enter number of heads@uni-chanel/offset")
        validator = QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression(
                r"([1-9]\d{0,2})?(@[1-9]\d{0,2}(-(([1-5]\d{1,2})|([1-9]\d{0,1}))(\/([1-3]\d{1,2}|[1-9]))?)?)?"))

        self._patching = QtWidgets.QLineEdit("")
        self._patching.setValidator(validator)
        self._patching.textChanged.connect(self._validate_input)
        patching_layout.addWidget(_patching_node)
        patching_layout.addWidget(self._patching)

        error_layout = QtWidgets.QHBoxLayout()
        self._error_label = QtWidgets.QLabel("no Error Found")
        error_layout.addWidget(self._error_label)

        layout_exit = QtWidgets.QHBoxLayout()
        self._ok = QtWidgets.QPushButton()
        self._ok.setText("patch")
        _cancel = QtWidgets.QPushButton()
        _cancel.setText("cancel")
        layout_exit.addWidget(_cancel)
        layout_exit.addWidget(self._ok)
        _cancel.setAutoDefault(False)
        self._ok.setAutoDefault(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_fixture)
        layout.addLayout(patching_layout)
        layout.addLayout(error_layout)
        layout.addLayout(layout_exit)

        # TODO Hier sollte noch ein nummernblock hin
        self.setLayout(layout)
        self._ok.clicked.connect(self._accept)
        _cancel.clicked.connect(self._reject)

        for mode in self._fixture['modes']:
            self._select_mode.addItem(mode['name'])
        self._select_mode.setCurrentIndex(fixture[1])

    @property
    def patching_information(self) -> PatchingInformation:
        """property of used Fixture"""
        return self._patching_information

    def set_error(self, text: str):
        """update Error Label"""
        self._error_label.setText(text)

    def _update_used_fixture(self) -> None:
        self._patching_information.used_fixture = make_used_fixture(self._fixture, self._select_mode.currentIndex(),
                                                                    self.patching_information.universe)
        self._validate_input()

    def _accept(self) -> None:
        """accept the Fixture"""
        self.accept()

    def _reject(self) -> None:
        """cancel Patching"""
        self.reject()

    def _validate_input(self) -> None:
        """validate the patching String and update count, universe, channel and offset"""
        patching = self._patching.text()
        if patching == "":
            patching = "1"
        if patching[0] == "@":
            patching = "1" + patching
        spliter = list(filter(None, re.split('[@/]|-', patching)))
        spliter += [0] * (4 - len(spliter))
        spliter = list(map(int, spliter))
        self._patching_information.count = spliter[0]
        self._patching_information.universe = spliter[1] - 1 if spliter[1] > 0 else 0
        self._patching_information.channel = spliter[2] - 1 if spliter[2] > 0 else 0
        self._patching_information.offset = spliter[3]
        channel_count = len(self._patching_information.used_fixture.mode['channels'])

        self._ok.setEnabled(False)
        if 0 < self._patching_information.offset < channel_count:
            self._error_label.setText("offset to low")
            return
        if self.patching_information.channel > 512 - (channel_count * self.patching_information.count):
            self._error_label.setText("not enough channels")
            return

        self._error_label.setText("No Error Found")
        self._ok.setEnabled(True)
