"""Tab for the Dimmer Director's groups."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from model.filters._channel_names import is_valid_channel_name
from model.filters.dimmer_director import DimmerGroup

if TYPE_CHECKING:
    from model.filters.dimmer_director import DimmerDirectorFilter


_COLUMN_LABELS = ["Name", "X", "Y", "Z", "#Mixins", "#Offsets", "phase_x", "phase_y", "phase_z"]


class GroupsTab(QWidget):
    """Edits the list of groups via a flat table (one group per row)."""

    groups_changed = Signal()

    def __init__(self, model: DimmerDirectorFilter, parent: QWidget | None = None) -> None:
        """Build the layout and populate the table from the model."""
        super().__init__(parent)
        self._model = model
        self._in_rebuild = False
        layout = QVBoxLayout()
        button_row = QHBoxLayout()
        self._add_btn = QPushButton("Add Group")
        self._add_btn.clicked.connect(self._add_group)
        button_row.addWidget(self._add_btn)
        self._remove_btn = QPushButton("Remove Group")
        self._remove_btn.clicked.connect(self._remove_group)
        self._remove_btn.setEnabled(False)
        button_row.addWidget(self._remove_btn)
        button_row.addStretch()
        layout.addLayout(button_row)
        self._table = QTableWidget()
        self._table.setColumnCount(len(_COLUMN_LABELS))
        self._table.setHorizontalHeaderLabels(_COLUMN_LABELS)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(_COLUMN_LABELS)):
            self._table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self._table.itemSelectionChanged.connect(self._selection_changed)
        self._table.itemChanged.connect(self._cell_edited)
        layout.addWidget(self._table)
        self.setLayout(layout)
        self._refresh_table()
        self._input_dialog: QInputDialog | QMessageBox | None = None

    def _refresh_table(self) -> None:
        """Rebuild the table from the current model state."""
        self._in_rebuild = True
        try:
            groups = self._model.groups
            self._table.setRowCount(len(groups))
            for row, group in enumerate(groups):
                values = [
                    group.name,
                    str(group.x),
                    str(group.y),
                    str(group.z),
                    str(group.n_mix_group),
                    str(group.n_off_group),
                    str(group.phase_x),
                    str(group.phase_y),
                    str(group.phase_z),
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if col == 0:
                        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self._table.setItem(row, col, item)
        finally:
            self._in_rebuild = False

    def _selection_changed(self) -> None:
        """Enable the remove button when a row is selected."""
        self._remove_btn.setEnabled(self._table.currentRow() >= 0)

    def _cell_edited(self, item: QTableWidgetItem) -> None:
        """Apply a numeric cell edit back to the model."""
        if self._in_rebuild:
            return
        row = item.row()
        col = item.column()
        groups = self._model.groups
        if not 0 <= row < len(groups):
            return
        group = groups[row]
        text = item.text()
        try:
            value = int(text)
        except ValueError:
            self._refresh_table()
            return
        updated = DimmerGroup(
            name=group.name,
            x=group.x,
            y=group.y,
            z=group.z,
            n_mix_group=group.n_mix_group,
            n_off_group=group.n_off_group,
            phase_x=group.phase_x,
            phase_y=group.phase_y,
            phase_z=group.phase_z,
        )
        match col:
            case 1:
                updated.x = max(1, value)
            case 2:
                updated.y = max(1, value)
            case 3:
                updated.z = max(1, value)
            case 4:
                updated.n_mix_group = max(0, value)
            case 5:
                updated.n_off_group = max(0, value)
            case 6:
                updated.phase_x = value
            case 7:
                updated.phase_y = value
            case 8:
                updated.phase_z = value
        if not self._model.update_group(row, updated):
            self._refresh_table()
            return
        self._refresh_table()
        self.groups_changed.emit()

    def _add_group(self) -> None:
        """Open an input dialog to name and add a new group."""
        if self._input_dialog is not None:
            self._input_dialog.deleteLater()
        dialog = QInputDialog(self)
        dialog.setModal(True)
        dialog.setLabelText("Please input group name:")
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.accepted.connect(self._add_group_final)
        self._input_dialog = dialog
        dialog.show()

    def _add_group_final(self) -> None:
        """Commit the name from the input dialog to the model."""
        dialog = self._input_dialog
        if not isinstance(dialog, QInputDialog):
            return
        name = dialog.textValue().strip()
        dialog.deleteLater()
        self._input_dialog = None
        if not is_valid_channel_name(name):
            self._show_error(
                "Invalid Group Name",
                "Group names must not be empty, must be unique and may only contain ASCII letters, digits, "
                "single underscores and hyphens. Double underscores and trailing underscores are not allowed.",
            )
            return
        if self._model.add_group(name) is None:
            self._show_error("Invalid Group Name", "The provided name is already in use.")
            return
        self._refresh_table()
        self.groups_changed.emit()

    def _remove_group(self) -> None:
        """Remove the currently selected group."""
        row = self._table.currentRow()
        if row < 0:
            return
        if self._model.remove_group(row):
            self._refresh_table()
            self.groups_changed.emit()

    def _show_error(self, title: str, message: str) -> None:
        """Show a non-blocking error dialog."""
        if self._input_dialog is not None:
            self._input_dialog.deleteLater()
        self._input_dialog = QMessageBox(self)
        self._input_dialog.setWindowTitle(title)
        self._input_dialog.setText(message)
        self._input_dialog.setIcon(QMessageBox.Icon.Critical)
        self._input_dialog.show()
