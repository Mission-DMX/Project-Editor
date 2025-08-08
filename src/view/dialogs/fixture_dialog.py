"""Dialog for editing Fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

import style
from model.universe import NUMBER_OF_CHANNELS

if TYPE_CHECKING:
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QWidget

    from model import BoardConfiguration
    from model.ofl.fixture import UsedFixture


class FixtureDialog(QDialog):
    """Dialog for editing Fixtures."""

    def __init__(self, fixture: UsedFixture, board_configuration: BoardConfiguration, parent: QWidget = None) -> None:
        """Dialog for editing Fixtures."""
        super().__init__(parent)
        self._fixture: UsedFixture = fixture
        self._board_configuration: BoardConfiguration = board_configuration

        layout = QVBoxLayout()

        layout_fixture = QGridLayout()
        layout_fixture.addWidget(QLabel("Fixture name:"), 0, 0)
        layout_fixture.addWidget(
            QLabel(self._fixture.short_name if self._fixture.short_name else self._fixture.name), 0, 1
        )

        layout_fixture.addWidget(QLabel("Anzeigename"), 1, 0)
        self._name_on_stage = QLineEdit(self._fixture.name_on_stage)
        layout_fixture.addWidget(self._name_on_stage, 1, 1)

        layout_fixture.addWidget(QLabel("Start Index"), 2, 0)
        self._start_index = QSpinBox()
        self._start_index.setMinimum(1)
        self._start_index.setMaximum(NUMBER_OF_CHANNELS)
        self._start_index.setValue(self._fixture.start_index + 1)
        self._start_index.textChanged.connect(self._validate_input)
        layout_fixture.addWidget(self._start_index, 2, 1)

        self._color_label = QLabel("Anzeigefarbe")
        self._selected_color = self._fixture.color_on_stage
        self._color_label.setStyleSheet(f"background-color: {self._fixture.color_on_stage.name()};")
        layout_fixture.addWidget(self._color_label, 3, 0)
        color_button = QPushButton("Farbe wählen")
        color_button.clicked.connect(self._open_color_picker)
        layout_fixture.addWidget(color_button, 3, 1)

        layout_error = QHBoxLayout()
        self._error_label = QLabel("No Error Found!")
        self._error_label.setFixedHeight(20)
        self._error_label.setStyleSheet(style.LABEL_OKAY)
        layout_error.addWidget(self._error_label)

        layout_exit = QHBoxLayout()
        self._ok_button = QPushButton()
        self._ok_button.setText("Okay")
        self._ok_button.clicked.connect(self._ok)
        _cancel_button = QPushButton()
        _cancel_button.setText("cancel")
        _cancel_button.clicked.connect(self._cancel)
        layout_exit.addWidget(_cancel_button)
        layout_exit.addWidget(self._ok_button)

        layout.addLayout(layout_fixture)
        layout.addLayout(layout_error)
        layout.addLayout(layout_exit)
        self.setLayout(layout)

    def _ok(self) -> None:
        """Handle OK clicked."""
        self._fixture.color_on_stage = self._selected_color
        self._fixture.start_index = int(self._start_index.text()) - 1
        self._fixture.name_on_stage = self._name_on_stage.text()
        self.accept()

    def _cancel(self) -> None:
        """Handle Cancel clicked."""
        self.reject()

    def _open_color_picker(self) -> None:
        """Open Color picker."""
        dialog = QColorDialog(self)
        dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)

        dialog.colorSelected.connect(self._color_chosen)
        dialog.open()

    def _color_chosen(self, color: QColor) -> None:
        """Handle color chosen."""
        self._selected_color = color
        self._color_label.setStyleSheet(f"background-color: {color.name()};")

    def _validate_input(self) -> None:
        """Validate input."""
        self._ok_button.setEnabled(False)
        occupied = np.arange(
            int(self._start_index.value() - 1), int(self._start_index.value() - 1) + self._fixture.channel_length
        )

        if np.isin(occupied, self._board_configuration.get_occupied_channels(self._fixture.universe)).any():
            self._error_label.setText("Channels already occupied!")
            self._error_label.setStyleSheet(style.LABEL_ERROR)
            return

        self._error_label.setText("No Error Found!")
        self._error_label.setStyleSheet(style.LABEL_OKAY)
        self._ok_button.setEnabled(True)
