"""Dialog for editing Fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QWidget

    from model.ofl.fixture import UsedFixture


class FixtureDialog(QDialog):
    """Dialog for editing Fixtures."""

    def __init__(self, fixture: UsedFixture, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._fixture: UsedFixture = fixture

        layout = QVBoxLayout()

        layout_fixture = QGridLayout()
        layout_fixture.addWidget(QLabel("Fixture name:"), 0, 0)
        layout_fixture.addWidget(QLabel(self._fixture.short_name), 0, 1)

        layout_fixture.addWidget(QLabel("Anzeigename"), 1, 0)
        self._name_on_stage = QLineEdit(self._fixture.name_on_stage)
        layout_fixture.addWidget(self._name_on_stage, 1, 1)

        layout_fixture.addWidget(QLabel("Start Index"), 2, 0)
        self._start_index = QLineEdit(str(self._fixture.start_index + 1))
        layout_fixture.addWidget(self._start_index, 2, 1)

        self._color_label = QLabel("Anzeigefarbe")
        self._selected_color = self._fixture.color_on_stage
        self._color_label.setStyleSheet(f"background-color: {self._fixture.color_on_stage.name()};")
        layout_fixture.addWidget(self._color_label, 3, 0)
        color_button = QPushButton("Farbe wählen")
        color_button.clicked.connect(self._open_color_picker)
        layout_fixture.addWidget(color_button, 3, 1)

        layout_exit = QHBoxLayout()
        _ok_button = QPushButton()
        _ok_button.setText("Okay")
        _ok_button.clicked.connect(self._ok)
        _cancel_button = QPushButton()
        _cancel_button.setText("cancel")
        _cancel_button.clicked.connect(self._cancel)
        layout_exit.addWidget(_cancel_button)
        layout_exit.addWidget(_ok_button)

        layout.addLayout(layout_fixture)
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
