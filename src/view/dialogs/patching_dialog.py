"""Dialog for Patching Fixture."""

import re
from dataclasses import dataclass

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

import style
from model import BoardConfiguration
from model.ofl.fixture import make_used_fixture
from model.ofl.ofl_fixture import OflFixture


@dataclass
class PatchingInformation:
    """Information for Patching."""

    def __init__(self, fixture: OflFixture) -> None:
        """Information for Patching."""
        self._fixture: OflFixture = fixture
        self.count: int = 0
        self.universe: int = 0
        self.channel: int = 0
        self.offset: int = 0

    @property
    def fixture(self) -> OflFixture:
        """OFL Fixture."""
        return self._fixture


class PatchingDialog(QtWidgets.QDialog):
    """Dialog for Patching Fixture."""

    def __init__(
        self, board_configuration: BoardConfiguration, fixture: tuple[OflFixture, int], parent: object = None
    ) -> None:
        """Dialog for Patching Fixture."""
        super().__init__(parent)
        # Create widgets
        self._board_configuration = board_configuration
        self._patching_information = PatchingInformation(fixture[0])

        layout_fixture = QtWidgets.QHBoxLayout()
        self._select_mode = QtWidgets.QComboBox()
        self._select_mode.currentIndexChanged.connect(self._validate_input)
        layout_fixture.addWidget(QtWidgets.QLabel(fixture[0].name))
        layout_fixture.addWidget(self._select_mode)

        patching_layout = QtWidgets.QHBoxLayout()
        _patching_node = QtWidgets.QLabel("Enter number of heads@uni-chanel/offset")
        validator = QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression(
                r"([1-9]\d{0,2})?"
                r"(@[1-9]\d{0,2}"
                r"(-(([5][0]\d)|(51[0-2])|([1-4]\d{1,2})|([1-9]\d{0,1}))"
                r"(\/(([5][0]\d)|(51[0-2])|([1-4]\d{1,2})|([1-9]\d{0,1})))?)?)?"
            )
        )

        self._patching = QtWidgets.QLineEdit("")
        self._patching.setValidator(validator)
        self._patching.textChanged.connect(self._validate_input)
        patching_layout.addWidget(_patching_node)
        patching_layout.addWidget(self._patching)

        error_layout = QtWidgets.QHBoxLayout()
        self._error_label = QtWidgets.QLabel("No Error Found!")
        self._error_label.setStyleSheet(style.LABEL_OKAY)
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

        for mode in self._patching_information.fixture.modes:
            self._select_mode.addItem(mode.name)
        self._select_mode.setCurrentIndex(fixture[1])

    @property
    def patching_information(self) -> PatchingInformation:
        """Patching Information."""
        return self._patching_information

    def generate_fixtures(self) -> None:
        """Generate a used Fixture list from Patching information."""
        start_index = self.patching_information.channel
        for _ in range(self.patching_information.count):
            used_fixture = make_used_fixture(
                self._board_configuration,
                self._patching_information.fixture,
                self._select_mode.currentIndex(),
                self.patching_information.universe,
                start_index,
            )

            if self._patching_information.offset == 0:
                start_index += used_fixture.channel_length
            else:
                start_index += self._patching_information.offset

    def _accept(self) -> None:
        """Handle Accept button."""
        self.accept()

    def _reject(self) -> None:
        """Handle Cancel button."""
        self.reject()

    def _validate_input(self) -> None:
        """Validate the patching String and update count, universe, channel and offset."""
        patching = self._patching.text()
        if patching == "":
            patching = "1"
        if patching[0] == "@":
            patching = "1" + patching
        spliter = list(filter(None, re.split("[@/]|-", patching)))
        spliter += [0] * (4 - len(spliter))
        spliter = list(map(int, spliter))
        self._patching_information.count = spliter[0]
        self._patching_information.universe = spliter[1] - 1 if spliter[1] > 0 else 0
        self._patching_information.channel = spliter[2] - 1 if spliter[2] > 0 else 0
        self._patching_information.offset = spliter[3]
        channel_count = len(self._patching_information.fixture.modes[self._select_mode.currentIndex()].channels)

        self._ok.setEnabled(False)
        if not self._board_configuration.universe(self._patching_information.universe):
            self._error_label.setText("No matching Universe!")
            self._error_label.setStyleSheet(style.LABEL_ERROR)
            return
        if 0 < self._patching_information.offset < channel_count:
            self._error_label.setText("Offset to low!")
            self._error_label.setStyleSheet(style.LABEL_ERROR)
            return

        start_index = self.patching_information.channel
        offset = self._patching_information.offset or channel_count

        block_starts = np.arange(self._patching_information.count) * offset + start_index
        channel_offsets = np.arange(channel_count)
        occupied = (block_starts[:, np.newaxis] + channel_offsets).ravel()

        if occupied[-1] > 511:
            self._error_label.setText("Not enough channels!")
            self._error_label.setStyleSheet(style.LABEL_ERROR)
            return

        if np.isin(
            occupied, self._board_configuration.get_occupied_channels(self._patching_information.universe)
        ).any():
            self._error_label.setText("Channels already occupied!")
            self._error_label.setStyleSheet(style.LABEL_ERROR)
            return

        self._error_label.setText("No Error Found!")
        self._error_label.setStyleSheet(style.LABEL_OKAY)
        self._ok.setEnabled(True)
