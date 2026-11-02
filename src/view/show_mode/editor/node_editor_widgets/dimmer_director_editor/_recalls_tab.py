"""Recalls tab: one row per recall, two columns per group (effect, dimmer)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from model.filters.dimmer_director import DimmerDirectorFilter


class RecallsTab(QWidget):
    """Edit the saved recalls as a flat table."""

    def __init__(self, model: DimmerDirectorFilter, parent: QWidget | None = None) -> None:
        """Build the layout and seed the table."""
        super().__init__(parent)
        self._model = model
        self._in_rebuild = False
        layout = QVBoxLayout()
        buttons = QHBoxLayout()
        add_btn = QPushButton("Add Recall")
        add_btn.clicked.connect(self._add_recall)
        buttons.addWidget(add_btn)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_recall)
        buttons.addWidget(remove_btn)
        buttons.addStretch()
        layout.addLayout(buttons)
        self._table = QTableWidget()
        self._table.itemChanged.connect(self._cell_edited)
        layout.addWidget(self._table)
        self.setLayout(layout)
        self.update_recall_table()
        self._model.configuration_changed.mapped_signal.connect(self.update_recall_table)

    def update_recall_table(self) -> None:
        """Rebuild the recall table from the model (headers follow current groups)."""
        self._in_rebuild = True
        try:
            groups = self._model.groups
            recalls = self._model.recalls
            self._table.setRowCount(len(recalls))
            self._table.setColumnCount(1 + 2 * len(groups))
            headers: list[str] = ["#"]
            for g in groups:
                headers.append(f"{g.name} effect")
                headers.append(f"{g.name} dimmer")
            self._table.setHorizontalHeaderLabels(headers)
            for row, recall in enumerate(recalls):
                index_item = QTableWidgetItem(str(row))
                index_item.setFlags(index_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row, 0, index_item)
                for group_idx in range(len(groups)):
                    if group_idx < len(recall.selections):
                        eff, dim = recall.selections[group_idx]
                    else:
                        eff, dim = 0, 0
                    eff_item = QTableWidgetItem(str(eff))
                    eff_item.setData(Qt.ItemDataRole.UserRole, (row, group_idx, "effect"))
                    self._table.setItem(row, 1 + group_idx * 2, eff_item)
                    dim_item = QTableWidgetItem(str(dim))
                    dim_item.setData(Qt.ItemDataRole.UserRole, (row, group_idx, "dimmer"))
                    self._table.setItem(row, 2 + group_idx * 2, dim_item)
        finally:
            self._in_rebuild = False

    def _cell_edited(self, item: QTableWidgetItem) -> None:
        """Push a numeric recall cell edit into the model."""
        if self._in_rebuild:
            return
        payload = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(payload, tuple) or len(payload) != 3:
            return
        row, group_idx, kind = payload
        try:
            value = max(0, int(item.text()))
        except ValueError:
            self.update_recall_table()
            return
        recalls = self._model.recalls
        if not 0 <= row < len(recalls):
            return
        selections = recalls[row].selections
        current_eff, current_dim = selections[group_idx] if group_idx < len(selections) else (0, 0)
        if kind == "effect":
            self._model.set_recall_selection(row, group_idx, value, current_dim)
        else:
            self._model.set_recall_selection(row, group_idx, current_eff, value)

    def _add_recall(self) -> None:
        self._model.add_recall()

    def _remove_recall(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        self._model.remove_recall(row)
